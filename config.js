// PUBG نۇپۇز سىستېمىسى - ئاساسىي سەپلىمە ھۆججىتى
// ئۆزىڭىزنىڭ Supabase ۋە Telegram ئۇچۇرلىرىنى مۇشۇ يەرگە كىرگۈزۈڭ

const CONFIG = {
  // Supabase پۈتۈن تەڭشەكلىرى (Project Settings -> API دىن ئېلىنىدۇ)
  SUPABASE_URL: "https://your-project.supabase.co",
  SUPABASE_ANON_KEY: "your-anon-key",
  
  // Storage Bucket ئىسمى (schema.sql دا قۇرۇلغان bucket نامى)
  STORAGE_BUCKET: "screenshots",

  // تېلېگرامما بوت تەڭشەكلىرى (@BotFather دىن ئېلىنىدۇ)
  TELEGRAM_BOT_TOKEN: "your-bot-token",
  
  // باشقۇرغۇچىنىڭ Telegram Chat ID ياكى Group ID سى (@userinfobot ئارقىلىق بىلگىلى بولىدۇ)
  TELEGRAM_CHAT_ID: "your-chat-id",

  // باشقۇرغۇچى بېتىنىڭ (admin.html) كىرىش كودى (PIN)
  ADMIN_PIN: "8888"
};
