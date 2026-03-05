"use strict";

let staffTrendChart = null;
let adminCompareChart = null;
let dashboardInitialized = false;

function initToasts() {
  const stack = document.querySelector("[data-toast-stack]");
  if (!stack) {
    return;
  }

  const toasts = Array.from(stack.querySelectorAll("[data-toast]"));
  toasts.slice(3).forEach((toast) => {
    toast.remove();
  });

  stack.querySelectorAll("[data-toast-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const toast = button.closest("[data-toast]");
      if (toast) {
        toast.remove();
      }
    });
  });

  setTimeout(() => {
    stack.querySelectorAll("[data-toast]").forEach((toast) => {
      toast.remove();
    });
  }, 4000);
}

function initBellMenu() {
  const root = document.querySelector("[data-bell-root]");
  if (!root) {
    return;
  }

  const toggle = root.querySelector("[data-bell-toggle]");
  const menu = root.querySelector("[data-bell-menu]");
  if (!toggle || !menu) {
    return;
  }

  toggle.addEventListener("click", () => {
    menu.classList.toggle("is-open");
  });

  document.addEventListener("click", (event) => {
    if (!root.contains(event.target)) {
      menu.classList.remove("is-open");
    }
  });
}

async function fetchJson(url) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest"
    }
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function renderStaffTrendChart(payload) {
  const canvas = document.getElementById("staff-trend-chart");
  if (!canvas || typeof window.Chart === "undefined") {
    return;
  }

  canvas.setAttribute("dir", "ltr");
  const context = canvas.getContext("2d");
  if (!context) {
    return;
  }

  if (staffTrendChart) {
    staffTrendChart.destroy();
    staffTrendChart = null;
  }

  staffTrendChart = new window.Chart(context, {
    type: "bar",
    data: {
      labels: payload.labels,
      datasets: [
        {
          label: "Reports",
          data: payload.series,
          backgroundColor: "rgba(13, 148, 136, 0.82)",
          borderRadius: 6
        },
        {
          type: "line",
          label: "Target",
          data: payload.target_series,
          borderColor: "#F59E0B",
          borderDash: [6, 4],
          pointRadius: 2,
          tension: 0.2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          position: "bottom"
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

function renderStaffLeaderboard(rows) {
  const body = document.getElementById("staff-leaderboard-body");
  if (!body) {
    return;
  }

  if (!Array.isArray(rows) || rows.length === 0) {
    body.innerHTML = '<tr><td class="empty-cell" colspan="5">No data</td></tr>';
    return;
  }

  body.innerHTML = rows
    .map((row) => {
      const className = row.is_current_user ? " class=\"is-current-user\"" : "";
      return (
        `<tr${className}>` +
        `<td>${row.rank}</td>` +
        `<td>${row.display_name}</td>` +
        `<td>${row.ytd_total}</td>` +
        `<td>${row.avg_monthly}</td>` +
        `<td>${row.achievement_pct}%</td>` +
        "</tr>"
      );
    })
    .join("");
}

async function initStaffDashboard() {
  const container = document.getElementById("staff-dashboard");
  if (!container || dashboardInitialized) {
    return;
  }

  dashboardInitialized = true;
  const year = Number(container.dataset.year || new Date().getFullYear());

  try {
    const [stats, leaderboard] = await Promise.all([
      fetchJson(`/api/my-stats?year=${year}`),
      fetchJson(`/api/leaderboard?year=${year}`)
    ]);
    renderStaffTrendChart(stats);
    renderStaffLeaderboard(leaderboard);
  } catch (error) {
    console.error("Failed loading staff dashboard", error);
    dashboardInitialized = false;
  }
}

function renderAdminComparison(payload) {
  const canvas = document.getElementById("admin-compare-chart");
  if (!canvas || typeof window.Chart === "undefined") {
    return;
  }

  canvas.setAttribute("dir", "ltr");
  const context = canvas.getContext("2d");
  if (!context) {
    return;
  }

  if (adminCompareChart) {
    adminCompareChart.destroy();
    adminCompareChart = null;
  }

  const palette = ["#0D9488", "#2563EB", "#F59E0B", "#DC2626", "#7C3AED"];
  const datasets = (payload.datasets || []).map((dataset, index) => ({
    label: dataset.name,
    data: dataset.values,
    borderColor: palette[index % palette.length],
    backgroundColor: "transparent",
    pointRadius: 3,
    borderWidth: 2,
    tension: 0.2
  }));

  adminCompareChart = new window.Chart(context, {
    type: "line",
    data: {
      labels: payload.labels,
      datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          position: "bottom"
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

async function initAdminDashboard() {
  const container = document.getElementById("admin-dashboard");
  if (!container) {
    return;
  }

  const picker = document.getElementById("compare-picker");
  const button = picker ? picker.querySelector("[data-compare-load]") : null;
  if (!picker || !button) {
    return;
  }

  const year = Number(container.dataset.year || new Date().getFullYear());

  button.addEventListener("click", async () => {
    const selected = Array.from(
      picker.querySelectorAll("[data-compare-user]:checked")
    ).map((checkbox) => checkbox.value);

    if (selected.length === 0) {
      return;
    }

    try {
      const payload = await fetchJson(
        `/api/compare?users=${selected.join(",")}&year=${year}`
      );
      renderAdminComparison(payload);
    } catch (error) {
      console.error("Failed loading comparison data", error);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initToasts();
  initBellMenu();
  initStaffDashboard();
  initAdminDashboard();
});
