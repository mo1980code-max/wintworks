/* ============================================================
   Ibadah — Central site data (defaults)
   يتم تحميل هذا الملف أولاً، ثم تُدمج أي تعديلات محفوظة من
   لوحة الإدارة (admin.html) المخزنة في localStorage.
   ============================================================ */

window.IBADAH_DEFAULTS = {
  general: {
    siteName: "مركز العبادة الإسلامي",
    siteNameEn: "IBADAH ISLAMIC CENTER",
    slogan: "بيت لكل مسلم",
    phone: "+20 100 000 0000",
    email: "info@ibadah-center.org",
    address: "شارع السلام، المدينة المنورة",
    workingHours: "السبت - الخميس: 9ص - 9م",
    heroTitle: "اللّه خيرُ الرّازقين",
    heroSubtitle: "عندما تصبح الأمور صعبة، تراجع قليلاً وعدّ نِعَمك بدلاً من القلق، ثم توجّه إلى المسجد واطلب العون بالصبر والصلاة.",
    heroCta1: "اكتشف الدورات",
    heroCta2: "تبرّع الآن",
    aboutText: "منذ عام 1998 ونحن نخدم مجتمعنا المحلي بالعلم والعبادة والعمل الخيري، ونؤمن أن رسالتنا الأساسية هي تلبية احتياجات المجتمع المحلي، من تعليم القرآن وتجويده إلى رعاية الأيتام وإفطار الصائمين.",
    aboutText2: "يضم مركزنا مسجداً جامعاً، ومعهداً لتحفيظ القرآن، وقاعات للدورات، ومكتبة إسلامية مفتوحة، وفريقاً متطوعاً يعمل على مدار الساعة لخدمة المحتاجين."
  },

  /* إعدادات حساب مواقيت الصلاة (المنهج + المذهب) */
  prayerSettings: {
    method: "MWL",       // MWL | ISNA | Egypt | Makkah | Karachi | Tehran | Jeddah
    asrMadhab: "Shafi",  // Shafi | Hanafi
    defaultCityId: "makkah",
    iqamaOffsets: { Fajr: 30, Dhuhr: 15, Asr: 15, Maghrib: 0, Isha: 15 },
    jumuaTime: "12:30"
  },

  cities: [
    { id: "makkah",    name: "مكة المكرمة",      lat: 21.4225, lng: 39.8262, tz: "Asia/Riyadh" },
    { id: "madinah",   name: "المدينة المنورة",  lat: 24.4672, lng: 39.6111, tz: "Asia/Riyadh" },
    { id: "riyadh",    name: "الرياض",           lat: 24.7136, lng: 46.6753, tz: "Asia/Riyadh" },
    { id: "jeddah",    name: "جدة",              lat: 21.4858, lng: 39.1925, tz: "Asia/Riyadh" },
    { id: "cairo",     name: "القاهرة",          lat: 30.0444, lng: 31.2357, tz: "Africa/Cairo" },
    { id: "alexandria",name: "الإسكندرية",       lat: 31.2001, lng: 29.9187, tz: "Africa/Cairo" },
    { id: "dubai",     name: "دبي",              lat: 25.2048, lng: 55.2708, tz: "Asia/Dubai" },
    { id: "doha",      name: "الدوحة",           lat: 25.2854, lng: 51.5310, tz: "Asia/Qatar" },
    { id: "amman",     name: "عمّان",            lat: 31.9539, lng: 35.9106, tz: "Asia/Amman" },
    { id: "beirut",    name: "بيروت",            lat: 33.8938, lng: 35.5018, tz: "Asia/Beirut" },
    { id: "baghdad",   name: "بغداد",            lat: 33.3152, lng: 44.3661, tz: "Asia/Baghdad" },
    { id: "istanbul",  name: "إسطنبول",          lat: 41.0082, lng: 28.9784, tz: "Europe/Istanbul" },
    { id: "london",    name: "لندن",             lat: 51.5074, lng: -0.1278, tz: "Europe/London" },
    { id: "paris",     name: "باريس",            lat: 48.8566, lng: 2.3522,  tz: "Europe/Paris" },
    { id: "berlin",    name: "برلين",            lat: 52.5200, lng: 13.4050, tz: "Europe/Berlin" },
    { id: "newyork",   name: "نيويورك",          lat: 40.7128, lng: -74.0060, tz: "America/New_York" },
    { id: "toronto",   name: "تورونتو",          lat: 43.6532, lng: -79.3832, tz: "America/Toronto" }
  ],

  /* أسباب التبرع والحملات */
  causes: [
    {
      id: "iftar", title: "إفطار الصائمين", category: "رمضان",
      desc: "ساهم في توفير وجبات إفطار ساخنة لأكثر من 500 صائم يومياً خلال شهر رمضان المبارك.",
      goal: 50000, raised: 42500, img: "assets/img/cause-food.jpg"
    },
    {
      id: "orphans", title: "كفالة الأيتام", category: "كفالة",
      desc: "كفل يتيماً بالكامل؛ تشمل الرعاية الصحية والتعليمية والسكنية لمدة عام كامل.",
      goal: 36000, raised: 21400, img: "assets/img/about-quran.jpg"
    },
    {
      id: "education", title: "تعليم الأطفال", category: "تعليم",
      desc: "دعم معهد تحفيظ القرآن وتعليم اللغة العربية لأطفال الأسر المحتاجة.",
      goal: 28000, raised: 19300, img: "assets/img/cause-education.jpg"
    },
    {
      id: "water", title: "مشروع الماء", category: "بنية تحتية",
      desc: "حفر بئر ماء نظيف يخدم قرية كاملة بالتعاون مع المؤسسات الخيرية المحلية.",
      goal: 15000, raised: 6800, img: "assets/img/hero-3.jpg"
    },
    {
      id: "mosque", title: "صيانة المسجد", category: "المسجد",
      desc: "صيانة الفراش والإنارة وأنظمة التكييف وتجديد دورات المياه بالمسجد الجامع.",
      goal: 22000, raised: 15500, img: "assets/img/hero-2.jpg"
    },
    {
      id: "zakat", title: "صندوق الزكاة", category: "زكاة",
      desc: "صرف الزكاة في مصارفها الشرعية الثمانية على المستحقين من أسر المجتمع.",
      goal: 60000, raised: 39800, img: "assets/img/event-iftar.jpg"
    }
  ],

  /* الدورات */
  courses: [
    {
      id: "quran-intermediate", title: "دورة القرآن المتوسطة — إخوان", category: "قرآن",
      desc: "مراجعة وتثبيت الحفظ مع دراسة أحكام التجويد تطبيقياً، ومنهج أسبوعي واضح.",
      price: 16, priceFree: true, weeks: 10, enroll: 50, img: "assets/img/course-quran.jpg",
      teacher: "الشيخ حبيب النور", teacherRole: "عالم لغة عربية", teacherImg: "assets/img/about-manuscript.jpg"
    },
    {
      id: "tajweed", title: "أحكام التجويد للمبتدئين", category: "تجويد",
      desc: "تعلّم مخارج الحروف وأحكام النون الساكنة والمدود بأسلوب مبسط وممتع.",
      price: 20, priceFree: false, weeks: 8, enroll: 64, img: "assets/img/course-quran.jpg",
      teacher: "الشيخ عبد الرحمن ياسين", teacherRole: "قارئ ومجاز", teacherImg: "assets/img/about-manuscript.jpg"
    },
    {
      id: "calligraphy", title: "الخط العربي وتراثه", category: "فنون",
      desc: "دورة عملية في الخطوط الكلاسيكية (النسخ، الثلث، الديواني) مع أدوات الخط.",
      price: 35, priceFree: false, weeks: 12, enroll: 32, img: "assets/img/course-calligraphy.jpg",
      teacher: "الأستاذ مصطفى كمال", teacherRole: "خطّاط محترف", teacherImg: "assets/img/about-manuscript.jpg"
    },
    {
      id: "arabic", title: "اللغة العربية للناطقين بغيرها", category: "لغة",
      desc: "منهج تفاعلي لتعلم القراءة والكتابة والمحادثة العربية من الصفر حتى الإتقان.",
      price: 45, priceFree: false, weeks: 16, enroll: 41, img: "assets/img/cause-education.jpg",
      teacher: "د. سارة العتيبي", teacherRole: "أستاذة لغة عربية", teacherImg: "assets/img/about-manuscript.jpg"
    }
  ],

  /* الفعاليات */
  events: [
    {
      id: "ramadan-iftar", title: "مائدة الإفطار المجتمعية الكبرى", category: "رمضان",
      date: "2026-03-10T17:30:00", location: "القاعة الكبرى — المركز", image: "assets/img/event-iftar.jpg",
      desc: "أمسية رمضانية تجمع العائلات على مائدة إفطار واحدة، تليها صلاة التراويح ودروس قصيرة في فضائل الشهر.",
      guests: "د. أحمد الشرقاوي", organizer: "لجنة الشؤون الاجتماعية"
    },
    {
      id: "quran-competition", title: "مسابقة القرآن الكريم السنوية", category: "مسابقة",
      date: "2026-04-18T19:00:00", location: "مصلى الرجال — الدور الثاني", image: "assets/img/hero-2.jpg",
      desc: "مسابقة في الحفظ والتلاوة على مستويات متعددة، مع لجنة تحكيم من القراء المجازين وجوائز قيمة للفائزين.",
      guests: "الشيخ خالد المنتصر", organizer: "معهد التحفيظ"
    },
    {
      id: "family-lecture", title: "محاضرة الأسرة: تربية الأبناء على القيم", category: "محاضرة",
      date: "2026-09-12T18:00:00", location: "قاعة المحاضرات", image: "assets/img/hero-2.jpg",
      desc: "محاضرة تفاعلية مع جلسة أسئلة وأجوبة حول أساليب التربية الإسلامية المعاصرة والتواصل الفعال مع الأبناء.",
      guests: "د. منى الحسن", organizer: "لجنة الأسرة والمرأة"
    },
    {
      id: "volunteer-day", title: "يوم التطوع المجتمعي", category: "تطوع",
      date: "2026-09-26T09:00:00", location: "ساحة المركز", image: "assets/img/cause-food.jpg",
      desc: "يوم مفتوح للعمل التطوعي: توزيع مواد غذائية، وزيارة دور الرعاية، وحملة نظافة للحي، بانتظار مشاركتكم.",
      guests: "طاقم المتطوعين", organizer: "لجنة التطوع"
    }
  ],

  /* خطط الأسعار (دعم / اشتراكات المركز) */
  pricing: [
    { id: "basic", name: "عضوية عادية", price: 25, period: "شهرياً",
      features: ["حضور جميع الصلوات والجمعة", "الوصول إلى المكتبة", "خصم 10% على الدورات"] },
    { id: "family", name: "عضوية عائلية", price: 60, period: "شهرياً", featured: true,
      features: ["كل مزايا العضوية العادية", "حتى 6 أفراد", "خصم 25% على الدورات", "أولوية في التسجيل بالفعاليات", "مشاركة في جلسات دعم الأسرة"] },
    { id: "patron", name: "الراعي الدائم", price: 150, period: "شهرياً",
      features: ["كل مزايا العضوية العائلية", "تقرير سنوي عن أثر تبرعاتك", "دعوة خاصة للفعاليات الكبرى", "استشارة زكاة مجانية"] }
  ],

  /* أخبار */
  news: [
    { date: "26 رمضان 1447", title: "رحلة تأمل ومراجعة للقرآن الكريم في العشر الأواخر", excerpt: "برنامج يومي لمراجعة الحفظ وقيام الليل مع نخبة من القراء المجازين.", img: "assets/img/course-quran.jpg", author: "إدارة المركز" },
    { date: "18 رمضان 1447", title: "افتتاح شعبة جديدة لتحفيظ الأطفال بالحاسوب التفاعلي", excerpt: "قاعات مجهزة بأحدث أدوات التعليم التفاعلي لتعليم تلاوة القرآن برواية حفص.", img: "assets/img/cause-education.jpg", author: "معهد التحفيظ" },
    { date: "07 رمضان 1447", title: "تقرير أثر التبرعات: 1200 أسرة استفادت من مشروع الإفطار", excerpt: "تعرف على أرقام المشروع وتوزيع الوجبات ومجالات التوسعة القادمة.", img: "assets/img/cause-food.jpg", author: "لجنة الزكاة" }
  ],

  /* آيات (شرائح) */
  ayat: [
    { text: "يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ", ref: "البقرة (153)" },
    { text: "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ", ref: "الرعد (28)" },
    { text: "وَمَا تَفْعَلُوا مِنْ خَيْرٍ فَإِنَّ اللَّهَ بِهِ عَلِيمٌ", ref: "البقرة (215)" },
    { text: "إِنَّ اللَّهَ يَأْمُرُ بِالْعَدْلِ وَالْإِحْسَانِ وَإِيتَاءِ ذِي الْقُرْبَىٰ", ref: "النحل (90)" },
    { text: "وَقُولُوا لِلنَّاسِ حُسْنًا", ref: "البقرة (83)" }
  ],

  /* أركان الإسلام */
  pillars: [
    { ar: "الشهادتان", en: "Shahadah", img: "assets/img/hero-2.jpg" },
    { ar: "الصلاة", en: "Salah", img: "assets/img/hero-1.jpg" },
    { ar: "الزكاة", en: "Zakah", img: "assets/img/event-iftar.jpg" },
    { ar: "الصوم", en: "Sawm", img: "assets/img/event-iftar.jpg" },
    { ar: "الحج", en: "Hajj", img: "assets/img/hero-3.jpg" }
  ]
};

/* دالة دمج: الإعدادات الافتراضية + التعديلات المحفوظة في لوحة الإدارة */
window.getSiteData = function () {
  var raw = localStorage.getItem("ibadah-site-data");
  if (!raw) return JSON.parse(JSON.stringify(IBADAH_DEFAULTS));
  try {
    var saved = JSON.parse(raw);
    var merged = JSON.parse(JSON.stringify(IBADAH_DEFAULTS));
    Object.keys(saved || {}).forEach(function (key) {
      if (saved[key] && typeof saved[key] === "object" && !Array.isArray(saved[key])) {
        merged[key] = Object.assign({}, merged[key], saved[key]);
      } else {
        merged[key] = saved[key];
      }
    });
    return merged;
  } catch (e) {
    return JSON.parse(JSON.stringify(IBADAH_DEFAULTS));
  }
};

window.saveSiteData = function (data) {
  localStorage.setItem("ibadah-site-data", JSON.stringify(data));
};

window.resetSiteData = function () {
  localStorage.removeItem("ibadah-site-data");
};
