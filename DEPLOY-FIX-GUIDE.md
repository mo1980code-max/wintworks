# إصلاح الموقع على Vercel — دليل سريع

> **المشكلة:** موقعك `al-bayan-sage.vercel.app` يعرض صفحات فقط بدون تنسيق لأن مجلدات
> `css/` و`js/` و`data/` و`assets/` لم تُرفع معها (كلها تعطي 404).
> **السبب:** الرفع السابق ضمّن ملفات HTML فقط، أو رُفع مجلد داخل مجلد.
> **الحل:** إعادة النشر من الحزمة المسطّحة `al-bayan-vercel-deploy.zip` التالية (دقيقتان).

---

## الخطوات (المسار الأسرع — نفس الرابط)

1. حمّل **`al-bayan-vercel-deploy.zip`** (2.7 MB) وفُكّ ضغطه.
   → بعد الفك يجب أن ترى مباشرة: `index.html` و `css/` و `js/` و `data/` و `assets/` (مجلدات ظاهرة، وليس مجلدًا واحدًا يضمّها).

2. افتح `https://vercel.com/new` وسجّل دخولك.

3. **اسحب المجلد المفكوك** (محتوياته: index.html + المجلدات) على منطقة "Import Project".

4. Framework preset: **Other** → اضغط **Deploy**.

5. بعد ثوانٍ تحصل على رابط جديد يعمل بشكل كامل. **للاحتفاظ برابط `al-bayan-sage` القديم:**
   - احذف المشروع القديم: Project → Settings → General → **Danger Zone → Delete Project**.
   - أعِد تسمية المشروع الجديد إلى `al-bayan-sage` (Settings → General → Project Name).
   - الرابط يعود `https://al-bayan-sage.vercel.app` ويعمل الآن بتنسيق كامل.

## التحقق بعد النشر

- افتح `https://<اسمك>.vercel.app/css/style.css` → يجب أن يظهر كود CSS (وليس 404).
- افتح الصفحة الرئيسية: يجب أن تظهر الألوان، الصور، المواقيت، والعدّادات.

---

## مسار بديل (الأفضل للمستقبل — Git)

1. في Vercel: **Add New → Project → Import Git Repository** → اختر `mo1980code-max/wintworks`.
2. **Root Directory:** `al-bayan` — **Branch:** `arena/01a05e40-wintworks`.
3. Framework preset: **Other** → Deploy.
4. الرابط يبقى ثابتًا، وأي تحديث مستقبلي على الفرع يُنشر تلقائيًا.

> ⚠️ لا تستخدم الفرع `main` — نسخة القالب الصحيحة موجودة على
> `arena/01a05e40-wintworks` داخل مجلد `al-bayan/`.

---

## ملاحظات

- لا ترفع ملف `al-bayan-offline.html` أو `site-images-preview.jpg` مع النشر — غير ضروريين (الأول للفحص المحلي والثاني لأوراق الرفع).
- `php/contact.php` لا يعمل على Vercel (استضافة ثابتة) — النموذج يعمل كتجريبي، والرسائل الحقيقية تحتاج استضافة PHP أو خدمة نماذج (موضحة في الدليل).
- الحزمة الأصلية الكاملة للبيع تبقى `al-bayan-demo.zip` — هذه الحزمة الجديدة **للنشر فقط**.

---

## English summary

**Problem:** `al-bayan-sage.vercel.app` shows unstyled pages because `css/`, `js/`, `data/` and `assets/` folders are missing on the server (404).

**Fix (2 minutes):** download `al-bayan-vercel-deploy.zip` (flat structure: index.html + folders at root), extract, drag the folder into `https://vercel.com/new`, Framework preset **Other**, click **Deploy**. To keep the same URL: delete the old project (Danger Zone), rename the new one to `al-bayan-sage`.

**Alternative (recommended):** Vercel → New Project → Import GitHub repo `mo1980code-max/wintworks` → Root Directory **`al-bayan`** → Branch **`arena/01a05e40-wintworks`** → Other → Deploy. Future updates deploy automatically.
