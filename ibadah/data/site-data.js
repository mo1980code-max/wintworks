/* ============================================================
   Ibadah — Central site data (defaults, English version)
   The UI is English (LTR); RTL support is fully preserved in the
   code (logical CSS properties + one-line <html dir="rtl"> switch).
   Loaded first, then merged with any admin edits (localStorage).
   ============================================================ */

window.IBADAH_DEFAULTS = {
  general: {
    siteName: "Ibadah Islamic Center",
    siteNameEn: "IBADAH ISLAMIC CENTER",
    slogan: "A home for every Muslim",
    phone: "+20 100 000 0000",
    email: "info@ibadah-center.org",
    address: "Peace Street, Al-Madinah",
    workingHours: "Sat – Thu: 9 AM – 9 PM",
    heroTitle: "Allah is the Best of Providers",
    heroSubtitle: "When things are too hard to handle, retreat & count your blessings instead — then turn to the mosque and seek help through patience and prayer.",
    heroCta1: "Discover Courses",
    heroCta2: "Donate Now",
    aboutText: "Since 1998 we have been serving our local community through knowledge, worship and charity. We believe our primary role is to meet the needs of the local community — from Quran teaching and tajweed to orphan care and feeding the hungry.",
    aboutText2: "Our center hosts a grand mosque, a Quran memorization institute, course halls and an open Islamic library, with a volunteer team working around the clock to support those in need."
  },

  /* Prayer calculation settings (method + madhab) */
  prayerSettings: {
    method: "MWL",
    asrMadhab: "Shafi",
    defaultCityId: "makkah",
    iqamaOffsets: { Fajr: 30, Dhuhr: 15, Asr: 15, Maghrib: 0, Isha: 15 },
    jumuaTime: "12:30"
  },

  cities: [
    { id: "makkah",    name: "Makkah",          lat: 21.4225, lng: 39.8262, tz: "Asia/Riyadh" },
    { id: "madinah",   name: "Madinah",         lat: 24.4672, lng: 39.6111, tz: "Asia/Riyadh" },
    { id: "riyadh",    name: "Riyadh",          lat: 24.7136, lng: 46.6753, tz: "Asia/Riyadh" },
    { id: "jeddah",    name: "Jeddah",          lat: 21.4858, lng: 39.1925, tz: "Asia/Riyadh" },
    { id: "cairo",     name: "Cairo",           lat: 30.0444, lng: 31.2357, tz: "Africa/Cairo" },
    { id: "alexandria",name: "Alexandria",      lat: 31.2001, lng: 29.9187, tz: "Africa/Cairo" },
    { id: "dubai",     name: "Dubai",           lat: 25.2048, lng: 55.2708, tz: "Asia/Dubai" },
    { id: "doha",      name: "Doha",            lat: 25.2854, lng: 51.5310, tz: "Asia/Qatar" },
    { id: "amman",     name: "Amman",           lat: 31.9539, lng: 35.9106, tz: "Asia/Amman" },
    { id: "beirut",    name: "Beirut",          lat: 33.8938, lng: 35.5018, tz: "Asia/Beirut" },
    { id: "baghdad",   name: "Baghdad",         lat: 33.3152, lng: 44.3661, tz: "Asia/Baghdad" },
    { id: "istanbul",  name: "Istanbul",        lat: 41.0082, lng: 28.9784, tz: "Europe/Istanbul" },
    { id: "london",    name: "London",          lat: 51.5074, lng: -0.1278, tz: "Europe/London" },
    { id: "paris",     name: "Paris",           lat: 48.8566, lng: 2.3522,  tz: "Europe/Paris" },
    { id: "berlin",    name: "Berlin",          lat: 52.5200, lng: 13.4050, tz: "Europe/Berlin" },
    { id: "newyork",   name: "New York",        lat: 40.7128, lng: -74.0060, tz: "America/New_York" },
    { id: "toronto",   name: "Toronto",         lat: 43.6532, lng: -79.3832, tz: "America/Toronto" }
  ],

  /* Donation causes & campaigns */
  causes: [
    { id: "iftar", title: "Iftar for the Fasting", category: "Ramadan",
      desc: "Provide hot iftar meals for more than 500 fasting people every day during Ramadan.",
      goal: 50000, raised: 42500, img: "assets/img/cause-food.jpg" },
    { id: "orphans", title: "Orphan Sponsorship", category: "Sponsorship",
      desc: "Sponsor an orphan fully — health, education and housing support for a whole year.",
      goal: 36000, raised: 21400, img: "assets/img/about-quran.jpg" },
    { id: "education", title: "Children's Education", category: "Education",
      desc: "Support the Quran institute and Arabic classes for children of underprivileged families.",
      goal: 28000, raised: 19300, img: "assets/img/cause-education.jpg" },
    { id: "water", title: "Water for Life Project", category: "Infrastructure",
      desc: "Drill a clean water well serving a whole village with local charity partners.",
      goal: 15000, raised: 6800, img: "assets/img/hero-3.jpg" },
    { id: "mosque", title: "Mosque Maintenance", category: "Mosque",
      desc: "Renew carpets, lighting, AC systems and restrooms at the grand mosque.",
      goal: 22000, raised: 15500, img: "assets/img/hero-2.jpg" },
    { id: "zakat", title: "Zakat Fund", category: "Zakat",
      desc: "Distribute zakat across its eight eligible categories to deserving families.",
      goal: 60000, raised: 39800, img: "assets/img/event-iftar.jpg" }
  ],

  /* Courses */
  courses: [
    { id: "quran-intermediate", title: "Quran Intermediate Course — Brothers", category: "Quran",
      desc: "Consolidate memorization with applied tajweed practice and a clear weekly plan.",
      price: 16, priceFree: true, weeks: 10, enroll: 50, img: "assets/img/course-quran.jpg",
      teacher: "Sheikh Habib Al Noor", teacherRole: "Arabic Scholar", teacherImg: "assets/img/about-manuscript.jpg" },
    { id: "tajweed", title: "Tajweed Rules for Beginners", category: "Tajweed",
      desc: "Learn articulation points, rules of noon sakinah and elongation in a simple way.",
      price: 20, priceFree: false, weeks: 8, enroll: 64, img: "assets/img/course-quran.jpg",
      teacher: "Sheikh Abdul Rahman Yasin", teacherRole: "Certified Qari", teacherImg: "assets/img/about-manuscript.jpg" },
    { id: "calligraphy", title: "Arabic Calligraphy & Heritage", category: "Arts",
      desc: "A hands-on course in classical scripts (Naskh, Thuluth, Diwani) with real tools.",
      price: 35, priceFree: false, weeks: 12, enroll: 32, img: "assets/img/course-calligraphy.jpg",
      teacher: "Master Mustafa Kamal", teacherRole: "Professional Calligrapher", teacherImg: "assets/img/about-manuscript.jpg" },
    { id: "arabic", title: "Arabic for Non-Native Speakers", category: "Language",
      desc: "Interactive curriculum to read, write and speak Arabic from zero to fluency.",
      price: 45, priceFree: false, weeks: 16, enroll: 41, img: "assets/img/cause-education.jpg",
      teacher: "Dr. Sara Al-Otaibi", teacherRole: "Arabic Language Professor", teacherImg: "assets/img/about-manuscript.jpg" }
  ],

  /* Events (with speaker / researcher bio) */
  events: [
    {
      id: "ramadan-iftar", title: "Grand Community Iftar Feast", category: "Ramadan",
      date: "2026-03-10T17:30:00", location: "Grand Hall — Main Building", image: "assets/img/event-iftar.jpg",
      desc: "An evening gathering families around one iftar table, followed by tarawih prayer and short talks on the virtues of Ramadan.",
      guests: "Dr. Ahmed El-Sharqawi", guestRole: "Social Affairs Advisor",
      guestBio: "PhD in Islamic Social Work; 15+ years leading family support and community welfare programs across the region.",
      organizer: "Social Affairs Committee", tags: ["Ramadan", "Family", "Iftar"]
    },
    {
      id: "quran-competition", title: "Annual Quran Recitation Competition", category: "Competition",
      date: "2026-04-18T19:00:00", location: "Main Prayer Hall — 2nd Floor", image: "assets/img/hero-2.jpg",
      desc: "A multi-level competition in memorization and recitation with a jury of certified reciters and valuable prizes.",
      guests: "Sheikh Khaled Al-Muntasir", guestRole: "Head of Jury",
      guestBio: "Certified reciter with ijazah in the ten qira'at; director of the center's Ijazah program since 2015.",
      organizer: "Memorization Institute", tags: ["Quran", "Competition", "Youth"]
    },
    {
      id: "family-lecture", title: "Family Lecture: Raising Children on Values", category: "Lecture",
      date: "2026-09-12T18:00:00", location: "Lecture Hall", image: "assets/img/hero-2.jpg",
      desc: "Interactive lecture with Q&A on contemporary Islamic parenting and effective communication with children.",
      guests: "Dr. Mona Al-Hassan", guestRole: "Family & Education Researcher",
      guestBio: "Researcher in Islamic education and family studies; author of 6 books on positive parenting; university lecturer since 2012.",
      organizer: "Family & Women's Committee", tags: ["Family", "Parenting", "Lecture"]
    },
    {
      id: "volunteer-day", title: "Community Volunteer Day", category: "Volunteering",
      date: "2026-09-26T09:00:00", location: "Center Courtyard", image: "assets/img/cause-food.jpg",
      desc: "Open volunteering day: food distribution, care home visits and a neighborhood cleanup — join us.",
      guests: "Volunteer Team", guestRole: "Lead Volunteers",
      guestBio: "A dedicated team of 120 trained volunteers who run weekly service programs and emergency relief.",
      organizer: "Volunteering Committee", tags: ["Volunteers", "Community", "Outreach"]
    }
  ],

  /* Pricing plans (center membership) */
  pricing: [
    { id: "basic", name: "Basic Membership", price: 25, period: "per month",
      features: ["Attend all prayers & Jumu'ah", "Full library access", "10% course discount"] },
    { id: "family", name: "Family Membership", price: 60, period: "per month", featured: true,
      features: ["All Basic benefits", "Up to 6 members", "25% course discount", "Priority event registration", "Family support sessions"] },
    { id: "patron", name: "Patron Membership", price: 150, period: "per month",
      features: ["All Family benefits", "Annual impact report", "VIP invites to major events", "Free zakat consultation"] }
  ],

  /* News / articles */
  news: [
    { date: "Ramadan 26, 1447", title: "Journey of Reflection — Last Ten Nights", excerpt: "A daily program to revise memorization and pray qiyam with certified reciters.", img: "assets/img/course-quran.jpg", author: "Center Administration" },
    { date: "Ramadan 18, 1447", title: "New Interactive Kids' Tajweed Wing Opened", excerpt: "Classrooms equipped with interactive tools for teaching Quran recitation (Hafs).", img: "assets/img/cause-education.jpg", author: "Memorization Institute" },
    { date: "Ramadan 7, 1447", title: "Impact Report: 1,200 Families Reached by Iftar Project", excerpt: "See the numbers, meal distribution and the upcoming expansion plans.", img: "assets/img/cause-food.jpg", author: "Zakat Committee" }
  ],

  /* Quran verses (Arabic text + English translation) */
  ayat: [
    { text: "يَا أَيُّهَا الَّذِينَ آمَنُوا اسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ",
      translation: "O you who have believed, seek help through patience and prayer. Indeed, Allah is with the patient.",
      ref: "Al-Baqarah (153)" },
    { text: "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
      translation: "Truly, in the remembrance of Allah do hearts find rest.",
      ref: "Ar-Ra'd (28)" },
    { text: "وَمَا تَفْعَلُوا مِنْ خَيْرٍ فَإِنَّ اللَّهَ بِهِ عَلِيمٌ",
      translation: "And whatever good you do — indeed, Allah is All-Aware of it.",
      ref: "Al-Baqarah (215)" },
    { text: "إِنَّ اللَّهَ يَأْمُرُ بِالْعَدْلِ وَالْإِحْسَانِ وَإِيتَاءِ ذِي الْقُرْبَىٰ",
      translation: "Indeed, Allah commands justice, excellence, and giving to close relatives.",
      ref: "An-Nahl (90)" }
  ],

  /* Media embeds — managed from the admin panel (Media tab).
     YouTube: paste any watch / youtu.be / embed URL, it is converted
     automatically to an embeddable URL. */
  media: [
    { type: "youtube", title: "Surah Al-Fatihah — Mishary Rashid Alafasy",
      url: "https://www.youtube.com/watch?v=5vO0mgZ2Dmk" },
    { type: "youtube", title: "Surah Yasin — Alafasy Daily Quran",
      url: "https://www.youtube.com/watch?v=CYcdeLGyJ-k" },
    { type: "vimeo", title: "Community Documentary — A Year at the Center",
      url: "https://vimeo.com/76979871" },
    { type: "soundcloud", title: "Audio Recitations — SoundCloud",
      url: "https://soundcloud.com/explore" }
  ],

  /* Global audio reciters for the Quran player */
  reciters: [
    { id: "ar.alafasy", name: "Mishary Rashid Alafasy" },
    { id: "ar.abdulbasitmurattal", name: "Abdul Basit (Murattal)" },
    { id: "ar.husary", name: "Mahmoud Khalil Al-Husary" },
    { id: "ar.hudhaify", name: "Ali Al-Hudhaify" },
    { id: "ar.mahermuaiqly", name: "Maher Al-Muaiqly" },
    { id: "ar.minshawi", name: "Mohamed Siddiq El-Minshawi" },
    { id: "ar.shaatree", name: "Abu Bakr Ash-Shaatree" }
  ],

  /* Five pillars of Islam */
  pillars: [
    { ar: "الشهادتان", en: "Shahadah", img: "assets/img/hero-2.jpg" },
    { ar: "الصلاة", en: "Salah", img: "assets/img/hero-1.jpg" },
    { ar: "الزكاة", en: "Zakah", img: "assets/img/event-iftar.jpg" },
    { ar: "الصوم", en: "Sawm", img: "assets/img/about-quran.jpg" },
    { ar: "الحج", en: "Hajj", img: "assets/img/hero-3.jpg" }
  ],

  /* Latest projects */
  projects: [
    { id: "quran-school", title: "Quran Memory School", category: "Education", status: "completed", progress: 100, year: "2025",
      desc: "A full day-school wing for 300 students with interactive tajweed classrooms.", img: "assets/img/cause-education.jpg" },
    { id: "water-well", title: "Water for Life — 12th Well", category: "Water", status: "in-progress", progress: 65, year: "2026",
      desc: "Drilling and equipping a clean water well for a rural village community.", img: "assets/img/hero-3.jpg" },
    { id: "iftar-kitchen", title: "Community Iftar Kitchen", category: "Relief", status: "in-progress", progress: 48, year: "2026",
      desc: "Central kitchen serving 1,000+ hot meals daily during Ramadan.", img: "assets/img/cause-food.jpg" },
    { id: "prayer-hall", title: "Prayer Hall Refurbishment", category: "Infrastructure", status: "completed", progress: 100, year: "2024",
      desc: "Renewed carpets, lighting and AC in the main prayer hall.", img: "assets/img/hero-2.jpg" }
  ]
};

/* Safe storage wrapper — works even when localStorage is blocked (file://) */
window.IBADAH_STORE = (function () {
  var mem = {};
  return {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return mem[k] || null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { mem[k] = v; } },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) { delete mem[k]; } }
  };
})();

/* Merge: defaults + admin edits (localStorage) */
window.getSiteData = function () {
  var raw = window.IBADAH_STORE.get("ibadah-site-data");
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
  window.IBADAH_STORE.set("ibadah-site-data", JSON.stringify(data));
};

window.resetSiteData = function () {
  window.IBADAH_STORE.del("ibadah-site-data");
};
