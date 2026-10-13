// ========================================================
// PUBG نۇپۇز سىستېمىسى: ئالدى تەرەپ (Frontend) مەنتىق كودى
// سۈرەت سىقىش، Supabase غا يۈكلەش ۋە Telegram غا ئۇقتۇرۇش يوللاش
// ========================================================

// 1. Supabase Client نى قۇرۇش
let supabaseClient = null;
if (typeof supabase !== 'undefined' && CONFIG && CONFIG.SUPABASE_URL && CONFIG.SUPABASE_ANON_KEY) {
  supabaseClient = supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);
}

// 2. كۆپ ئىشلىتىلىدىغان ئېلېمېنتلار
const form = document.getElementById('popularityForm');
const pubgIdInput = document.getElementById('pubgId');
const amountInput = document.getElementById('amount');
const contactInput = document.getElementById('contact');
const screenshotInput = document.getElementById('screenshot');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const removeImageBtn = document.getElementById('removeImageBtn');
const submitBtn = document.getElementById('submitBtn');
const btnSpinner = document.getElementById('btnSpinner');
const btnText = document.getElementById('btnText');
const alertModal = document.getElementById('alertModal');
const alertTitle = document.getElementById('alertTitle');
const alertMessage = document.getElementById('alertMessage');
const alertCloseBtn = document.getElementById('alertCloseBtn');
const presetButtons = document.querySelectorAll('.preset-btn');

let selectedFile = null;

// 3. نۇپۇز سانى تېز تاللاش كۇنۇپكىلىرى (Presets)
presetButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const val = btn.getAttribute('data-value');
    amountInput.value = val;
    presetButtons.forEach(b => {
      b.classList.remove('border-amber-400', 'bg-amber-400/20', 'text-amber-300');
      b.classList.add('border-slate-700', 'bg-slate-800/80', 'text-slate-300');
    });
    btn.classList.remove('border-slate-700', 'bg-slate-800/80', 'text-slate-300');
    btn.classList.add('border-amber-400', 'bg-amber-400/20', 'text-amber-300');
  });
});

amountInput.addEventListener('input', () => {
  presetButtons.forEach(b => {
    if (b.getAttribute('data-value') === amountInput.value) {
      b.classList.add('border-amber-400', 'bg-amber-400/20', 'text-amber-300');
      b.classList.remove('border-slate-700', 'bg-slate-800/80', 'text-slate-300');
    } else {
      b.classList.remove('border-amber-400', 'bg-amber-400/20', 'text-amber-300');
      b.classList.add('border-slate-700', 'bg-slate-800/80', 'text-slate-300');
    }
  });
});

// 4. سۈرەت كۆرۈش (Preview) ۋە تاللاش
screenshotInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    showAlert('ئەسكەرتىش', 'پەقەت رەسىم ھۆججىتى تاللىغىلى بولىدۇ (JPG, PNG).', 'warning');
    screenshotInput.value = '';
    return;
  }

  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (event) => {
    imagePreview.src = event.target.result;
    previewContainer.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
});

removeImageBtn.addEventListener('click', () => {
  selectedFile = null;
  screenshotInput.value = '';
  previewContainer.classList.add('hidden');
  imagePreview.src = '';
});

// 5. Canvas ئارقىلىق تور كۆرگۈچ ئىچىدە سۈرەتنى 500KB غا سىقىش (Compress Image)
async function compressImage(file, maxSizeKB = 500) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (event) => {
      const img = new Image();
      img.src = event.target.result;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        // ئەڭ چوڭ ئېنىقلىق نىسبىتىنى مۇۋاپىق بەلگىلەش (ئەڭ چوڭ تەرىپى 1280px دىن ئاشمىسۇن)
        const MAX_DIMENSION = 1280;
        if (width > height && width > MAX_DIMENSION) {
          height = Math.round((height * MAX_DIMENSION) / width);
          width = MAX_DIMENSION;
        } else if (height > MAX_DIMENSION) {
          width = Math.round((width * MAX_DIMENSION) / height);
          height = MAX_DIMENSION;
        }

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        // تەدرىجىي سۈپەتنى تەڭشەش
        let quality = 0.85;
        function attemptCompress() {
          canvas.toBlob((blob) => {
            if (!blob) {
              return reject(new Error('سۈرەتنى سىقىش مەغلۇپ بولدى'));
            }
            if (blob.size / 1024 <= maxSizeKB || quality <= 0.3) {
              resolve(blob);
            } else {
              quality -= 0.15;
              attemptCompress();
            }
          }, 'image/jpeg', quality);
        }
        attemptCompress();
      };
      img.onerror = (err) => reject(err);
    };
    reader.onerror = (err) => reject(err);
  });
}

// 6. تېلېگرامما بوتىغا كۇنۇپكىلىق ئۇچۇر ئەۋەتىش
async function sendTelegramNotification(submissionId, pubgId, amount, screenshotUrl, contactInfo) {
  if (!CONFIG.TELEGRAM_BOT_TOKEN || CONFIG.TELEGRAM_BOT_TOKEN === 'your-bot-token' ||
      !CONFIG.TELEGRAM_CHAT_ID || CONFIG.TELEGRAM_CHAT_ID === 'your-chat-id') {
    console.warn('تېلېگرامما بوت ئۇچۇرلىرى تەڭشەلمىگەن.');
    return;
  }

  const now = new Date().toLocaleString('ug-CN', { timeZone: 'Asia/Urumqi' }) || new Date().toLocaleString();
  const contactText = contactInfo ? `\n📞 <b>ئالاقە:</b> <code>${contactInfo}</code>` : '';

  const caption = 
`🔥 <b>يېڭى نۇپۇز (Popularity) ئەۋەتىلدى!</b>
🆔 <b>PUBG ID:</b> <code>${pubgId}</code>
💎 <b>نۇپۇز سانى:</b> <b>${Number(amount).toLocaleString()}</b>${contactText}
📅 <b>ۋاقتى:</b> ${now}
🔢 <b>رەت نومۇرى:</b> #${submissionId}`;

  const replyMarkup = {
    inline_keyboard: [
      [
        { text: '✅ تەستىقلاش', callback_data: `approve_${submissionId}` },
        { text: '❌ رەت قىلىش', callback_data: `reject_${submissionId}` }
      ]
    ]
  };

  try {
    if (screenshotUrl) {
      // سۈرەتلىك ئۇچۇر (sendPhoto)
      const photoApiUrl = `https://api.telegram.org/bot${CONFIG.TELEGRAM_BOT_TOKEN}/sendPhoto`;
      await fetch(photoApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: CONFIG.TELEGRAM_CHAT_ID,
          photo: screenshotUrl,
          caption: caption,
          parse_mode: 'HTML',
          reply_markup: replyMarkup
        })
      });
    } else {
      // سۈرەتسىز ئۇچۇر (sendMessage)
      const msgApiUrl = `https://api.telegram.org/bot${CONFIG.TELEGRAM_BOT_TOKEN}/sendMessage`;
      await fetch(msgApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: CONFIG.TELEGRAM_CHAT_ID,
          text: caption,
          parse_mode: 'HTML',
          reply_markup: replyMarkup
        })
      });
    }
  } catch (error) {
    console.error('تېلېگراممىغا ئۇچۇر ئەۋەتىشتە خاتالىق كۆرۈلدى:', error);
  }
}

// 7. جەدۋەلنى تاپشۇرۇش جەريانى
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const pubgId = pubgIdInput.value.trim();
  const amount = amountInput.value.trim();
  const contactInfo = contactInput.value.trim();

  // تەكشۈرۈش
  if (!pubgId || !/^\d+$/.test(pubgId)) {
    showAlert('خاتالىق', 'ئەسكەرتىش: PUBG كىملىكى پەقەت پۈتۈن سان بولۇشى كېرەك!', 'error');
    pubgIdInput.focus();
    return;
  }

  if (!amount || Number(amount) <= 0) {
    showAlert('خاتالىق', 'ئەسكەرتىش: توغرا بولغان نۇپۇز سانىنى كىرگۈزۈڭ!', 'error');
    amountInput.focus();
    return;
  }

  if (!selectedFile) {
    showAlert('خاتالىق', 'ئەسكەرتىش: نۇپۇز ئەۋەتكەنلىك ئىسپات سۈرىتىنى يۈكلەڭ!', 'error');
    return;
  }

  // تەڭشەك تەكشۈرۈش
  if (!supabaseClient || CONFIG.SUPABASE_URL.includes('your-project')) {
    showAlert('تەڭشەك كەمچىل', 'config.js ھۆججىتىدىكى Supabase ئادرېسى ۋە ئاچقۇچىنى تەڭشەڭ!', 'warning');
    return;
  }

  // كۇنۇپكىنى يۈكلىنىۋاتقان ھالەتكە كەلتۈرۈش
  setLoadingState(true);

  try {
    // 1) سۈرەتنى تور كۆرگۈچ ئىچىدە سىقىش (< 500KB)
    btnText.textContent = 'سۈرەت پىششىقلىنىۋاتىدۇ...';
    const compressedBlob = await compressImage(selectedFile, 500);

    // 2) Supabase Storage قا يۈكلەش
    btnText.textContent = 'سۈرەت ساقلىنىۋاتىدۇ...';
    const fileExt = 'jpg';
    const fileName = `${Date.now()}_${pubgId}_${Math.random().toString(36).substring(2, 7)}.${fileExt}`;
    const filePath = `uploads/${fileName}`;

    const { data: storageData, error: storageError } = await supabaseClient
      .storage
      .from(CONFIG.STORAGE_BUCKET || 'screenshots')
      .upload(filePath, compressedBlob, {
        contentType: 'image/jpeg',
        cacheControl: '3600',
        upsert: false
      });

    if (storageError) {
      console.error('Storage Error:', storageError);
      throw new Error('ئىسپات سۈرىتىنى يۈكلەش مەغلۇپ بولدى: ' + storageError.message);
    }

    // ئاشكارا سۈرەت ئۇلىنىشىنى ئېلىش
    const { data: publicUrlData } = supabaseClient
      .storage
      .from(CONFIG.STORAGE_BUCKET || 'screenshots')
      .getPublicUrl(filePath);

    const screenshotUrl = publicUrlData.publicUrl;

    // 3) Supabase ساندانغا خاتىرە قىستۇرۇش
    btnText.textContent = 'ئۇچۇر يوللىنىۋاتىدۇ...';
    const { data: insertData, error: insertError } = await supabaseClient
      .from('popularity_submissions')
      .insert([
        {
          pubg_id: pubgId,
          amount: Number(amount),
          contact_info: contactInfo || null,
          screenshot_url: screenshotUrl,
          status: 'pending'
        }
      ])
      .select();

    if (insertError) {
      console.error('Database Error:', insertError);
      throw new Error('ساندانغا ساقلاش مەغلۇپ بولدى: ' + insertError.message);
    }

    const insertedRecord = insertData[0];

    // 4) تېلېگرامما بوت ئارقىلىق باشقۇرغۇچىغا دەرھال ئۇقتۇرۇش قىلىش
    btnText.textContent = 'ئۇقتۇرۇش قىلىنىۋاتىدۇ...';
    await sendTelegramNotification(
      insertedRecord.id,
      pubgId,
      amount,
      screenshotUrl,
      contactInfo
    );

    // مۇۋەپپەقىيەت كۆرسىتىش
    showAlert(
      '🎉 تاپشۇرۇلدى!',
      `نۇپۇز ئۇچۇرىڭىز ۋە ئىسپاتىڭىز مۇۋەپپەقىيەتلىك تاپشۇرۇلدى!\n\nPUBG ID: ${pubgId}\nنۇپۇز: ${Number(amount).toLocaleString()}\n\nباشقۇرغۇچى تەستىقلىغاندىن كېيىن سىستېمىدا كۈچكە ئىگە بولىدۇ. رەھمەت!`,
      'success'
    );

    // جەدۋەلنى ئەسلىگە كەلتۈرۈش
    form.reset();
    selectedFile = null;
    previewContainer.classList.add('hidden');
    imagePreview.src = '';
    presetButtons.forEach(b => {
      b.classList.remove('border-amber-400', 'bg-amber-400/20', 'text-amber-300');
      b.classList.add('border-slate-700', 'bg-slate-800/80', 'text-slate-300');
    });

  } catch (err) {
    console.error('Submit error:', err);
    showAlert('خاتالىق كۆرۈلدى', err.message || 'ئۇچۇر تاپشۇرۇشتا كۈتۈلمىگەن مەسىلە كۆرۈلدى.', 'error');
  } finally {
    setLoadingState(false);
  }
});

// يۈكلىنىش كۇنۇپكىسىنىڭ ھالىتى
function setLoadingState(loading) {
  if (loading) {
    submitBtn.disabled = true;
    submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
    btnSpinner.classList.remove('hidden');
    btnText.textContent = 'بىر تەرەپ قىلىنىۋاتىدۇ...';
  } else {
    submitBtn.disabled = false;
    submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
    btnSpinner.classList.add('hidden');
    btnText.textContent = '🚀 نۇپۇز ئۇچۇرىنى تاپشۇرۇش';
  }
}

// ئەسكەرتىش دىئالوگى (Modal)
function showAlert(title, message, type = 'info') {
  alertTitle.textContent = title;
  alertMessage.innerText = message;
  
  if (type === 'success') {
    alertTitle.className = 'text-xl font-bold text-emerald-400';
  } else if (type === 'error') {
    alertTitle.className = 'text-xl font-bold text-rose-400';
  } else if (type === 'warning') {
    alertTitle.className = 'text-xl font-bold text-amber-400';
  } else {
    alertTitle.className = 'text-xl font-bold text-cyan-400';
  }

  alertModal.classList.remove('hidden');
  alertModal.classList.add('flex');
}

alertCloseBtn.addEventListener('click', () => {
  alertModal.classList.add('hidden');
  alertModal.classList.remove('flex');
});
