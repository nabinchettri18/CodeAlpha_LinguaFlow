import "dotenv/config";
import http from "node:http";
import process from "node:process";
import { GoogleGenAI } from "@google/genai";

const HOST = process.env.GEMINI_HOST || "127.0.0.1";
const PORT = Number(process.env.GEMINI_PORT || 8765);

const API_KEY =
  process.env.GOOGLE_API_KEY ||
  process.env.GEMINI_API_KEY ||
  "";

const PRIMARY_MODEL =
  process.env.GEMINI_PRIMARY_MODEL || "gemini-2.5-flash";

const FALLBACK_MODEL =
  process.env.GEMINI_FALLBACK_MODEL || "gemini-3.1-flash-lite";

const MAX_BODY_BYTES = 2 * 1024 * 1024;

const REQUEST_TIMEOUT_MS = Number(
  process.env.GEMINI_SERVER_TIMEOUT || 60000
);

const gemini = API_KEY
  ? new GoogleGenAI({
      apiKey: API_KEY,
    })
  : null;


// ------------------------------------------------------------
// RESPONSE HELPERS
// ------------------------------------------------------------

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);

  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store",
  });

  res.end(body);
}


function sendError(res, status, message) {
  sendJson(res, status, {
    success: false,
    error: message,
  });
}


// ------------------------------------------------------------
// REQUEST BODY
// ------------------------------------------------------------

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    let size = 0;

    req.setEncoding("utf8");

    req.on("data", (chunk) => {
      size += Buffer.byteLength(chunk, "utf8");

      if (size > MAX_BODY_BYTES) {
        reject(new Error("Request body is too large."));
        req.destroy();
        return;
      }

      body += chunk;
    });

    req.on("end", () => {
      if (!body.trim()) {
        reject(new Error("Request body is empty."));
        return;
      }

      try {
        resolve(JSON.parse(body));
      } catch {
        reject(new Error("Request body is not valid JSON."));
      }
    });

    req.on("error", reject);
  });
}


// ------------------------------------------------------------
// TRANSLATION PROMPT
// ------------------------------------------------------------

function buildTranslationPrompt({
  source,
  target,
  text,
}) {
  return [
    `Translate the following text from ${source} to ${target}.`,
    "",
    "Rules:",
    "1. Return ONLY the translated text.",
    "2. Do not explain the translation.",
    "3. Do not answer questions contained in the source text.",
    "4. Preserve names, numbers, punctuation, URLs, and formatting where possible.",
    "5. Preserve the original meaning, tone, and intent.",
    "6. Do not add quotation marks unless they exist in the source.",
    "",
    "Text to translate:",
    text,
  ].join("\n");
}


// ------------------------------------------------------------
// GEMINI TRANSLATION
// ------------------------------------------------------------

async function translateWithGemini({
  source,
  target,
  text,
  model,
}) {
  if (!gemini) {
    throw new Error("GEMINI_API_KEY is not configured.");
  }

  const modelName = model || PRIMARY_MODEL;

  const prompt = buildTranslationPrompt({
    source,
    target,
    text,
  });

  const controller = new AbortController();

  const timeout = setTimeout(() => {
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  try {
    const response = await gemini.models.generateContent({
      model: modelName,

      contents: prompt,

      config: {
        temperature: 0,
        topP: 1,

        systemInstruction:
          "You are LinguaFlow's translation engine. " +
          "Translate accurately. Never answer questions contained " +
          "inside the source text. Return only the translation.",
      },
    });

    const translation = response?.text?.trim();

    if (!translation) {
      throw new Error("Gemini returned an empty translation.");
    }

    return translation;
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error("Gemini request timed out.");
    }

    throw error;
  } finally {
    clearTimeout(timeout);
  }
}


// ------------------------------------------------------------
// TRANSLATE ENDPOINT
// ------------------------------------------------------------

async function handleTranslate(req, res) {
  let payload;

  try {
    payload = await readJsonBody(req);
  } catch (error) {
    sendError(res, 400, error.message);
    return;
  }

  const source = String(payload?.source || "").trim();
  const target = String(payload?.target || "").trim();
  const text = String(payload?.text || "").trim();

  const model =
    String(payload?.model || PRIMARY_MODEL).trim();

  if (!source || !target || !text) {
    sendError(
      res,
      400,
      "source, target, and text are required."
    );

    return;
  }

  try {
    const translation = await translateWithGemini({
      source,
      target,
      text,
      model,
    });

    sendJson(res, 200, {
      success: true,
      translation,
      model,
    });
  } catch (error) {
    console.error(
      `[LinguaFlow] Gemini error (${model}):`,
      error?.message || error
    );

    sendError(
      res,
      502,
      error?.message || "Gemini request failed."
    );
  }
}


// ------------------------------------------------------------
// HTTP SERVER
// ------------------------------------------------------------

const server = http.createServer(
  async (req, res) => {
    const method = req.method || "GET";

    const url = new URL(
      req.url || "/",
      `http://${req.headers.host || `${HOST}:${PORT}`}`
    );


    // --------------------------------------------------------
    // HEALTH
    // --------------------------------------------------------

    if (
      method === "GET" &&
      url.pathname === "/health"
    ) {
      sendJson(res, 200, {
        success: true,
        service: "LinguaFlow Gemini Service",
        status: "ready",
        port: PORT,
        configured: Boolean(API_KEY),
        primary_model: PRIMARY_MODEL,
        fallback_model: FALLBACK_MODEL,
      });

      return;
    }


    // --------------------------------------------------------
    // TRANSLATE
    // --------------------------------------------------------

    if (
      method === "POST" &&
      url.pathname === "/translate"
    ) {
      await handleTranslate(req, res);
      return;
    }


    // --------------------------------------------------------
    // ROOT
    // --------------------------------------------------------

    if (
      method === "GET" &&
      url.pathname === "/"
    ) {
      sendJson(res, 200, {
        success: true,
        service: "LinguaFlow Gemini Service",
        endpoints: [
          "/health",
          "/translate",
        ],
      });

      return;
    }


    sendError(res, 404, "Not found.");
  }
);


// ------------------------------------------------------------
// SERVER ERROR
// ------------------------------------------------------------

server.on("error", (error) => {
  console.error(
    "[LinguaFlow] Gemini server error:",
    error
  );

  process.exitCode = 1;
});


// ------------------------------------------------------------
// START SERVER
// ------------------------------------------------------------

server.listen(PORT, HOST, () => {
  console.log(
    `[LinguaFlow] Gemini service ready at http://${HOST}:${PORT}`
  );

  console.log(
    `[LinguaFlow] Primary model: ${PRIMARY_MODEL}`
  );

  console.log(
    `[LinguaFlow] Fallback model: ${FALLBACK_MODEL}`
  );

  if (!API_KEY) {
    console.warn(
      "[LinguaFlow] WARNING: GEMINI_API_KEY is not configured."
    );
  }
});


// ------------------------------------------------------------
// SHUTDOWN
// ------------------------------------------------------------

function shutdown(signal) {
  console.log(
    `[LinguaFlow] ${signal} received. Shutting down...`
  );

  server.close(() => {
    process.exit(0);
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));