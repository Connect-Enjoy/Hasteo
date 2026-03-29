/* ===== STUDENT DASHBOARD JAVASCRIPT ===== */

// ===== LIVE CLOCK =====
function updateClock() {
  const now = new Date();
  const h = now.getHours() % 12 || 12;
  const m = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
  const el = document.getElementById('clockTime');
  if (el) el.textContent = `${h}:${m}:${s} ${ampm}`;
}
setInterval(updateClock, 1000);
updateClock();

// ===== GENERATE STAR PARTICLES =====
function generateStars() {
  const container = document.getElementById('starsContainer');
  if (!container) return;
  const count = 80;
  for (let i = 0; i < count; i++) {
    const star = document.createElement('div');
    star.className = 'star';
    star.style.left = `${Math.random() * 100}%`;
    star.style.top = `${Math.random() * 100}%`;
    star.style.animationDelay = `${Math.random() * 4}s`;
    star.style.animationDuration = `${2 + Math.random() * 4}s`;
    const size = Math.random() < 0.3 ? 3 : Math.random() < 0.6 ? 2 : 1;
    star.style.width = `${size}px`;
    star.style.height = `${size}px`;
    container.appendChild(star);
  }
}
generateStars();

// ===== PROGRESS BAR ANIMATION =====
document.addEventListener('DOMContentLoaded', function () {
  setTimeout(() => {
    const fill = document.getElementById('progressFill');
    if (fill) {
      const pct = TOTAL_SCANS > 0 ? Math.min(100, Math.round((TOTAL_SCANS / Math.max(TOTAL_SCANS, 1)) * 100)) : 0;
      fill.style.width = pct + '%';
      const pctLabel = fill.closest('.sd-progress-section')?.querySelector('.label-pct');
      if (pctLabel) pctLabel.textContent = pct + '%';
    }
  }, 300);
});

// ===== ATTENDANCE MODAL =====
function openAttendanceModal() {
  const modal = document.getElementById('attendanceModal');
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
  renderAttendanceCalendar();
}

function closeAttendanceModal() {
  const modal = document.getElementById('attendanceModal');
  modal.classList.remove('open');
  document.body.style.overflow = '';
}

// Close on overlay click
document.addEventListener('DOMContentLoaded', function () {
  const overlay = document.getElementById('attendanceModal');
  if (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeAttendanceModal();
    });
  }

  // ESC to close
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAttendanceModal();
  });
});

// ===== RENDER ATTENDANCE CALENDAR =====
async function renderAttendanceCalendar() {
  const body = document.getElementById('attendanceModalBody');
  if (!body) return;

  body.innerHTML = `<div class="sd-loading"><div class="sd-spinner"></div><p>Loading attendance...</p></div>`;

  try {
    const res = await fetch('/api/student/attendance?student_id=' + encodeURIComponent(STUDENT_ID));
    const data = await res.json();

    if (!data.success) throw new Error(data.error || 'Failed to load');

    const scans = data.scans || [];
    body.innerHTML = buildCalendarHTML(scans, data.total, data.today);

  } catch (err) {
    // Fallback: render with no data
    body.innerHTML = buildCalendarHTML([], TOTAL_SCANS, TODAY_SCANS);
  }
}

function buildCalendarHTML(scans, total, todayCount) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const monthName = now.toLocaleString('default', { month: 'long' });

  // Build a set of scan dates
  const scanDates = new Set();
  scans.forEach(s => {
    const d = new Date(s.scan_date || s.scan_time);
    scanDates.add(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`);
  });

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = now.getDate();

  let presentCount = 0;
  let absentCount = 0;

  // Count days in month so far
  for (let d = 1; d < today; d++) {
    const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const dayOfWeek = new Date(year, month, d).getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) continue; // Skip weekends
    if (scanDates.has(dateKey)) presentCount++;
    else absentCount++;
  }

  const pct = (presentCount + absentCount) > 0
    ? Math.round((presentCount / (presentCount + absentCount)) * 100)
    : 0;

  let calHTML = `
    <div class="att-month-header">
      <div class="att-month-title">${monthName} ${year}</div>
      <div class="att-month-stats">
        <span class="att-stat-mini p"><i class="fas fa-circle" style="font-size:8px;"></i> ${presentCount} Present</span>
        <span class="att-stat-mini a"><i class="fas fa-circle" style="font-size:8px;"></i> ${absentCount} Absent</span>
      </div>
    </div>

    <div style="margin-bottom:20px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
        <span style="font-size:0.85rem;color:rgba(255,255,255,0.5)">Attendance Rate</span>
        <span style="font-size:1rem;font-weight:800;background:linear-gradient(135deg,#10b981,#06b6d4);-webkit-background-clip:text;background-clip:text;color:transparent">${pct}%</span>
      </div>
      <div class="sd-progress-bar">
        <div class="sd-progress-fill" style="width:${pct}%"></div>
      </div>
    </div>

    <div class="att-calendar">
      <div class="att-cal-head">Sun</div>
      <div class="att-cal-head">Mon</div>
      <div class="att-cal-head">Tue</div>
      <div class="att-cal-head">Wed</div>
      <div class="att-cal-head">Thu</div>
      <div class="att-cal-head">Fri</div>
      <div class="att-cal-head">Sat</div>
  `;

  // Empty cells before first day
  for (let i = 0; i < firstDay; i++) {
    calHTML += `<div class="att-cal-day empty"></div>`;
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const dayOfWeek = new Date(year, month, d).getDay();
    let cls = '';
    let title = '';

    if (d === today) {
      cls = 'today';
      title = 'Today';
    } else if (dayOfWeek === 0 || dayOfWeek === 6) {
      cls = 'holiday';
      title = 'Weekend';
    } else if (d > today) {
      cls = '';
    } else if (scanDates.has(dateKey)) {
      cls = 'present';
      title = 'Present';
    } else {
      cls = 'absent';
      title = 'Absent';
    }

    calHTML += `<div class="att-cal-day ${cls}" title="${title}">${d}</div>`;
  }

  calHTML += `</div>`;

  // Legend
  calHTML += `
    <div class="att-legend">
      <div class="att-legend-item"><div class="att-legend-dot p"></div> Present</div>
      <div class="att-legend-item"><div class="att-legend-dot a"></div> Absent</div>
      <div class="att-legend-item"><div class="att-legend-dot h"></div> Weekend</div>
      <div class="att-legend-item"><div class="att-legend-dot t"></div> Today</div>
    </div>
  `;

  // Recent scan list in modal
  if (scans.length > 0) {
    calHTML += `<div style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.06);padding-top:20px;">
      <div style="font-size:0.85rem;font-weight:700;color:rgba(255,255,255,0.7);margin-bottom:14px;display:flex;align-items:center;gap:8px;">
        <i class="fas fa-list"></i> Recent Scans
      </div>
      <div class="sd-scan-list">`;

    scans.slice(0, 8).forEach(scan => {
      const t = new Date(scan.scan_time);
      const timeStr = t.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
      const dateStr = t.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

      calHTML += `
        <div class="sd-scan-item">
          <div class="sd-scan-dot check-in"></div>
          <div class="sd-scan-info">
            <div class="scan-type">Bus ${scan.bus_number || 'N/A'}</div>
            <div class="scan-bus">${scan.branch || ''} · ${dateStr}</div>
          </div>
          <div class="sd-scan-time">${timeStr}</div>
        </div>`;
    });

    calHTML += `</div></div>`;
  }

  return calHTML;
}

// ===== AUTO-DISMISS FLASH MESSAGES =====
document.addEventListener('DOMContentLoaded', function () {
  const msgs = document.querySelectorAll('.sd-flash-msg');
  msgs.forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(20px)';
      msg.style.transition = 'all 0.3s ease';
      setTimeout(() => msg.remove(), 300);
    }, 4000);
  });
});

// ===== STAT COUNTER ANIMATION =====
function animateCounter(el, target, duration = 1200) {
  if (!el) return;
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

document.addEventListener('DOMContentLoaded', function () {
  setTimeout(() => {
    animateCounter(document.getElementById('totalScansVal'), TOTAL_SCANS);
    animateCounter(document.getElementById('todayScansVal'), TODAY_SCANS);
  }, 400);
});

// ===== ENTRANCE ANIMATIONS =====
document.addEventListener('DOMContentLoaded', function () {
  const cards = document.querySelectorAll('.sd-stat-card, .sd-card, .sd-hero');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, idx) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }, idx * 80);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach((card, idx) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(24px)';
    card.style.transition = `opacity 0.5s ease ${idx * 0.05}s, transform 0.5s cubic-bezier(0.23, 1, 0.32, 1) ${idx * 0.05}s`;
    observer.observe(card);
  });
});
