// PUBG نۇپۇز سىستېمىسى - ئاساسىي سەپلىمە ھۆججىتى
// ئۆزىڭىزنىڭ Supabase ۋە Telegram ئۇچۇرلىرىنى مۇشۇ يەرگە كىرگۈزۈڭ

const CONFIG = {
  // Supabase پۈتۈن تەڭشەكلىرى
  // ئەسكەرتىش: Supabase Project URL ئادەتتە https://xxxx.supabase.co شەكلىدە بولىدۇ.
  // ئاستىدىكى URL غا ئۆزىڭىزنىڭ Supabase تۈرىنىڭ Project URL ئادرېسىنى قويۇڭ (Settings -> Data API)
  SUPABASE_URL: "https://PROJECT_ID.supabase.co",
  SUPABASE_ANON_KEY: "sb_publishable_5Bqn-ZdZ_bmvBZTLYDsVXA_ZGkijOlC",
  
  // Storage Bucket ئىسمى (schema.sql دا قۇرۇلغان bucket نامى)
  STORAGE_BUCKET: "screenshots",

  // تېلېگرامما بوت تەڭشەكلىرى (@BotFather دىن ئېلىنغان)
  TELEGRAM_BOT_TOKEN: "8672194185:AAG3cor9idBuCOz8Qm84JUkwe1hLfRRpEYY",
  
  // باشقۇرغۇچىنىڭ Telegram Chat ID سى
  TELEGRAM_CHAT_ID: "6613680953",

  // باشقۇرغۇچى بېتىنىڭ (admin.html) كىرىش كودى (PIN)
  ADMIN_PIN: "8888"
};
