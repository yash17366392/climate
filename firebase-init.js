import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "AIzaSyAR2olaSiKiRcMKVL0FBMAg1VZ1bmdzCS0",
    authDomain: "eureka-ba3c5.firebaseapp.com",
    projectId: "eureka-ba3c5",
    storageBucket: "eureka-ba3c5.firebasestorage.app",
    messagingSenderId: "819553063484",
    appId: "1:819553063484:web:e4207d29d054044b6a2939",
    measurementId: "G-Y9MX2HF94R"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

// ── Admin emails (add more as needed) ──────────────────────────
export const ADMIN_EMAILS = [
  "yashpandiripalli@gmail.com"
];

export function isAdmin(user) {
  if (!user) return false;
  return ADMIN_EMAILS.includes(user.email.toLowerCase());
}

// ── Global logout ───────────────────────────────────────────────
window.logout = async () => {
    await signOut(auth);
    window.location.href = "/login.html";
};

// ── Profile completeness check (for Google sign-in users) ───────
// Pages that don't need this check
const NO_PROFILE_CHECK = ["/login.html", "/signup", "/complete-profile"];

export async function checkProfileComplete(user) {
  if (!user) return;
  const path = window.location.pathname;
  if (NO_PROFILE_CHECK.some(p => path.includes(p))) return;
  try {
    const { doc, getDoc } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
    const snap = await getDoc(doc(db, "users", user.uid, "profile", "info"));
    if (!snap.exists() || !snap.data().username) {
      window.location.href = "/complete-profile";
    }
  } catch {}
}

// ── Sidebar hydration ───────────────────────────────────────────
onAuthStateChanged(auth, (user) => {
    const nameEl      = document.getElementById("userName");
    const emailEl     = document.getElementById("userEmail");
    const navContainer = document.querySelector(".sidebar-nav");
    if (!nameEl || !emailEl || !navContainer) return;

    if (user) {
        nameEl.textContent  = user.displayName || "Researcher";
        emailEl.textContent = user.email;
        checkProfileComplete(user);

        // Show admin badge in sidebar if admin
        if (isAdmin(user) && !document.getElementById("adminBadge")) {
            const badge = document.createElement("span");
            badge.id = "adminBadge";
            badge.textContent = "Administrator";
            badge.style.cssText = `
                display:block;font-size:9px;font-weight:700;letter-spacing:0.15em;
                text-transform:uppercase;color:var(--gold);margin-top:2px;
            `;
            nameEl.parentElement.appendChild(badge);
        }

        if (!document.getElementById("logoutBtn")) {
            const a = document.createElement("a");
            a.id = "logoutBtn"; a.href = "#";
            a.onclick = e => { e.preventDefault(); window.logout(); };
            a.innerHTML = "🚪 &nbsp;Logout";
            navContainer.appendChild(a);
        }
    } else {
        nameEl.textContent  = "Guest";
        emailEl.textContent = "Not signed in";
        if (!document.querySelector('a[href="/login.html"]')) {
            const a = document.createElement("a");
            a.href = "/login.html"; a.innerHTML = "🔐 &nbsp;Login";
            navContainer.appendChild(a);
        }
    }
});
