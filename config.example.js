// ========================================================
// PUBG نۇپۇز سىستېمىسى: ئۈلگە سەپلىمە ھۆججىتى (Template Config)
// بۇ ھۆججەتنى كۆچۈرۈپ config.js قىلىپ ئۆزگەرتىپ، ئاستىدىكى قىممەتلەرنى توشقۇزۇڭ
// ========================================================

const CONFIG = {
  // 1. Supabase تەڭشەكلىرى (يېڭى تۈرنىڭ Settings -> API قىسمىدىن ئېلىنىدۇ)
  SUPABASE_URL: "https://your-new-project-id.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

  // 2. Storage قۇتىسىنىڭ نامى (schema.sql بويىچە 'screenshots' بولىدۇ)
  STORAGE_BUCKET: "screenshots",

  // 3. تېلېگرامما بوت ئاچقۇچى (@BotFather دىن ئېلىنغان Token)
  TELEGRAM_BOT_TOKEN: "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",

  // 4. باشقۇرغۇچىنىڭ تېلېگرامما ID سى (@userinfobot ئارقىلىق بىلىۋېلىڭ)
  TELEGRAM_CHAT_ID: "123456789",

  // 5. admin.html باشقۇرۇش بېتىنىڭ كىرىش كودى (PIN)
  ADMIN_PIN: "8888"
};
