/**
 * Calendar Accounts Manager
 * Manages the CALDAV_ACCOUNTS hidden input via a modal UI.
 * Each account card can load + toggle individual calendars.
 */

(function () {
    const TYPE_LABELS = {
        icloud: 'iCloud',
        google: 'Google',
        microsoft: 'Microsoft',
        webdav: 'WebDAV',
    };

    let accounts = [];

    // ── DOM refs ────────────────────────────────────────────────────────────────

    function refs() {
        return {
            overlay:    document.getElementById('cal-modal-overlay'),
            openBtn:    document.getElementById('open-cal-modal'),
            closeBtn:   document.getElementById('close-cal-modal'),
            doneBtn:    document.getElementById('cal-done-btn'),
            list:       document.getElementById('cal-account-list'),
            count:      document.getElementById('cal-account-count'),
            hidden:     document.querySelector('[name="CALDAV_ACCOUNTS"]'),
            typeSelect: document.getElementById('cal-type'),
            urlRow:     document.getElementById('cal-url-row'),
            urlInput:   document.getElementById('cal-url'),
            username:   document.getElementById('cal-username'),
            password:   document.getElementById('cal-password'),
            addBtn:     document.getElementById('cal-add-btn'),
            addError:   document.getElementById('cal-add-error'),
        };
    }

    // ── State helpers ───────────────────────────────────────────────────────────

    function loadFromHidden() {
        const r = refs();
        const raw = r.hidden ? r.hidden.value : '';
        if (!raw) { accounts = []; return; }
        try {
            const parsed = JSON.parse(raw);
            accounts = Array.isArray(parsed) ? parsed : [];
        } catch (_) {
            accounts = [];
        }
    }

    function saveToHidden() {
        const r = refs();
        if (r.hidden) {
            r.hidden.value = accounts.length ? JSON.stringify(accounts) : '';
        }
    }

    function updateCount() {
        const r = refs();
        if (!r.count) return;
        if (accounts.length === 0) {
            r.count.textContent = 'None configured';
        } else {
            r.count.textContent = accounts.length === 1
                ? '1 account'
                : `${accounts.length} accounts`;
        }
    }

    // ── Calendar listing ─────────────────────────────────────────────────────────

    async function fetchCalendars(account) {
        const resp = await fetch('/api/caldav-calendars', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Failed to load calendars');
        return data.calendars; // [{url, name}, …]
    }

    /**
     * Merge freshly-fetched server calendar list with any existing saved state.
     * Preserves enabled/disabled for calendars that already exist; defaults new
     * ones to enabled=true; removes calendars that no longer exist on the server.
     */
    function mergeCalendars(existing, fresh) {
        const existingMap = {};
        (existing || []).forEach(c => { existingMap[c.url] = c; });
        return fresh.map(c => ({
            url: c.url,
            name: c.name,
            enabled: existingMap[c.url] ? existingMap[c.url].enabled : true,
        }));
    }

    // ── Rendering ───────────────────────────────────────────────────────────────

    function renderCalendarList(calListEl, account, idx) {
        calListEl.innerHTML = '';

        const cals = account.calendars;
        if (!cals || cals.length === 0) return;

        cals.forEach((cal, calIdx) => {
            const row = document.createElement('label');
            row.className = 'cal-calendar-row';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = cal.enabled !== false;
            checkbox.className = 'cal-calendar-checkbox';
            checkbox.addEventListener('change', () => {
                accounts[idx].calendars[calIdx].enabled = checkbox.checked;
                saveToHidden();
            });

            const name = document.createElement('span');
            name.className = 'cal-calendar-name';
            name.textContent = cal.name || cal.url;

            row.appendChild(checkbox);
            row.appendChild(name);
            calListEl.appendChild(row);
        });
    }

    function buildAccountCard(account, idx) {
        const card = document.createElement('div');
        card.className = 'cal-account-card';

        // ── Card header ──────────────────────────────────────────────────────────
        const header = document.createElement('div');
        header.className = 'cal-card-header';

        const badge = document.createElement('span');
        badge.className = `cal-type-badge cal-badge-${account.type || 'webdav'}`;
        badge.textContent = TYPE_LABELS[account.type] || account.type;

        const info = document.createElement('div');
        info.className = 'cal-account-info';
        info.textContent = account.username || account.url || '(no username)';
        if (account.type === 'webdav' && account.url) {
            const sub = document.createElement('div');
            sub.className = 'cal-account-sub';
            sub.textContent = account.url;
            info.appendChild(sub);
        }

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'cal-remove-btn';
        removeBtn.textContent = 'Remove';
        removeBtn.addEventListener('click', () => {
            accounts.splice(idx, 1);
            saveToHidden();
            updateCount();
            renderList();
        });

        header.appendChild(badge);
        header.appendChild(info);
        header.appendChild(removeBtn);
        card.appendChild(header);

        // ── Calendar section ─────────────────────────────────────────────────────
        const calSection = document.createElement('div');
        calSection.className = 'cal-calendar-section';

        const calHeader = document.createElement('div');
        calHeader.className = 'cal-calendar-section-header';

        const calTitle = document.createElement('span');
        calTitle.className = 'cal-calendar-section-title';
        calTitle.textContent = 'Calendars';

        const loadBtn = document.createElement('button');
        loadBtn.type = 'button';
        loadBtn.className = 'cal-load-btn';
        loadBtn.textContent = account.calendars ? '↺ Reload' : 'Load';

        const statusEl = document.createElement('span');
        statusEl.className = 'cal-load-status';

        calHeader.appendChild(calTitle);
        calHeader.appendChild(loadBtn);
        calHeader.appendChild(statusEl);

        const calListEl = document.createElement('div');
        calListEl.className = 'cal-calendar-list';

        // Render any already-saved calendars immediately
        renderCalendarList(calListEl, account, idx);

        loadBtn.addEventListener('click', async () => {
            loadBtn.disabled = true;
            loadBtn.textContent = 'Loading…';
            statusEl.textContent = '';
            statusEl.className = 'cal-load-status';

            try {
                const fresh = await fetchCalendars(account);
                accounts[idx].calendars = mergeCalendars(accounts[idx].calendars, fresh);
                saveToHidden();
                renderCalendarList(calListEl, accounts[idx], idx);
                loadBtn.textContent = '↺ Reload';
                statusEl.textContent = `${fresh.length} calendar${fresh.length !== 1 ? 's' : ''}`;
            } catch (err) {
                statusEl.textContent = err.message;
                statusEl.className = 'cal-load-status cal-load-error';
                loadBtn.textContent = account.calendars ? '↺ Reload' : 'Load';
            } finally {
                loadBtn.disabled = false;
            }
        });

        calSection.appendChild(calHeader);
        calSection.appendChild(calListEl);
        card.appendChild(calSection);

        return card;
    }

    function renderList() {
        const r = refs();
        if (!r.list) return;
        r.list.innerHTML = '';

        if (accounts.length === 0) {
            const empty = document.createElement('p');
            empty.className = 'cal-empty-state';
            empty.textContent = 'No accounts added yet.';
            r.list.appendChild(empty);
            return;
        }

        accounts.forEach((acct, idx) => {
            r.list.appendChild(buildAccountCard(acct, idx));
        });
    }

    // ── URL field visibility ────────────────────────────────────────────────────

    function updateUrlVisibility() {
        const r = refs();
        if (!r.typeSelect || !r.urlRow) return;
        const isWebdav = r.typeSelect.value === 'webdav';
        r.urlRow.style.display = isWebdav ? 'block' : 'none';
        if (!isWebdav) r.urlInput.value = '';
    }

    // ── Add account ─────────────────────────────────────────────────────────────

    function addAccount() {
        const r = refs();
        const type = r.typeSelect.value;
        const username = r.username.value.trim();
        const password = r.password.value;
        const url = r.urlInput.value.trim();

        r.addError.hidden = true;
        r.addError.textContent = '';

        if (type === 'webdav' && !url) {
            showAddError('A Server URL is required for WebDAV accounts.');
            return;
        }
        if (!username) {
            showAddError('Username is required.');
            return;
        }
        if (!password) {
            showAddError('Password is required.');
            return;
        }

        const entry = { type, username, password };
        if (url) entry.url = url;

        accounts.push(entry);
        saveToHidden();
        updateCount();
        renderList();

        r.username.value = '';
        r.password.value = '';
        r.urlInput.value = '';
        r.typeSelect.value = 'icloud';
        updateUrlVisibility();
    }

    function showAddError(msg) {
        const r = refs();
        r.addError.textContent = msg;
        r.addError.hidden = false;
    }

    // ── Modal open / close ──────────────────────────────────────────────────────

    function openModal() {
        loadFromHidden();
        renderList();
        updateUrlVisibility();
        const r = refs();
        r.overlay.hidden = false;
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        const r = refs();
        r.overlay.hidden = true;
        document.body.style.overflow = '';
    }

    // ── Bootstrap ───────────────────────────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', () => {
        const r = refs();
        if (!r.overlay) return;

        loadFromHidden();
        updateCount();

        r.openBtn.addEventListener('click', openModal);
        r.closeBtn.addEventListener('click', closeModal);
        r.doneBtn.addEventListener('click', closeModal);

        r.overlay.addEventListener('click', (e) => {
            if (e.target === r.overlay) closeModal();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !r.overlay.hidden) closeModal();
        });

        r.typeSelect.addEventListener('change', updateUrlVisibility);
        r.addBtn.addEventListener('click', addAccount);

        document.addEventListener('configLoaded', () => {
            loadFromHidden();
            updateCount();
        });
    });
})();
