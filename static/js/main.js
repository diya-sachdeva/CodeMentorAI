// ─── API Helper ──────────────────────────────────────────────────────────────

async function api(method, url, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Something went wrong.");
  }
  return data;
}

// ─── Toast ───────────────────────────────────────────────────────────────────

let toastTimer;
function showToast(message, type = "info") {
  const toast = document.getElementById("toast");
  if (!toast) return;

  toast.textContent = message;
  toast.className = `show ${type}`;

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.className = "";
  }, 3500);
}

// ─── Auth Guard ───────────────────────────────────────────────────────────────

async function requireAuth() {
  try {
    const data = await api("GET", "/api/me");
    return data;
  } catch {
    window.location.href = "/login";
    return null;
  }
}

async function redirectIfAuthed() {
  try {
    await api("GET", "/api/me");
    window.location.href = "/dashboard";
  } catch {
    // Not logged in — good, stay on page
  }
}

// ─── Score Color ─────────────────────────────────────────────────────────────

function scoreColor(score) {
  if (score >= 80) return "var(--green)";
  if (score >= 60) return "var(--yellow)";
  return "var(--red)";
}

function assessmentBadge(assessment) {
  const map = {
    "Excellent": "green",
    "Good": "green",
    "Can Improve": "yellow",
    "Partial": "yellow",
    "Not Mentioned": "red",
    "Not Addressed": "red",
    "Incorrect": "red",
    "Clear": "green",
    "Adequate": "yellow",
    "Needs Improvement": "red",
  };
  const color = map[assessment] || "yellow";
  return `<span style="color: var(--${color}); font-weight: 600;">${assessment}</span>`;
}

function difficultyBadge(difficulty) {
  const cls = difficulty?.toLowerCase() || "medium";
  return `<span class="badge badge--${cls}">${difficulty}</span>`;
}

// ─── Logout ──────────────────────────────────────────────────────────────────

async function logout() {
  await api("POST", "/api/logout");
  window.location.href = "/";
}
