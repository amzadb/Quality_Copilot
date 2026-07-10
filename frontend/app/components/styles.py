"""Global styles matching the dashboard mockup."""

APP_CSS = """
body {
    background-color: #ececec !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.q-drawer {
    background: #ffffff !important;
}

.q-page-container {
    background: #ececec !important;
}

.q-layout {
    background: #ececec !important;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    cursor: pointer;
    color: #333;
    font-size: 15px;
    text-decoration: none;
    margin-bottom: 4px;
    transition: background 0.15s;
}

.nav-item:hover {
    background: #f0f0f0;
}

.nav-item.active {
    background: #e8e8e8;
    font-weight: 600;
}

.stat-card {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px 24px;
    min-width: 0;
    flex: 1;
}

.stat-label {
    display: block;
    color: #666;
    font-size: 14px;
    margin-bottom: 8px;
}

.stat-value {
    display: block;
    color: #111;
    font-size: 36px;
    font-weight: 700;
    line-height: 1.1;
}

.panel-card {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px 24px;
}

.badge-tests {
    background: #e8f5e9;
    color: #2e7d32;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-review {
    background: #e3f2fd;
    color: #1565c0;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-tests,
.badge-review {
    display: inline-block;
    line-height: 1.4;
}

.activity-row .q-label {
    margin: 0;
    padding: 0;
    line-height: normal;
}

.activity-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid #eee;
}

.activity-row:last-child {
    border-bottom: none;
}

.activity-title {
    flex: 1;
    font-size: 15px;
    color: #222;
    min-width: 0;
}

.activity-meta {
    color: #666;
    font-size: 14px;
    white-space: nowrap;
}

.activity-time {
    color: #888;
    font-size: 14px;
    white-space: nowrap;
    min-width: 80px;
    text-align: right;
}

.page-content {
    padding: 28px 32px;
    max-width: 1200px;
}

.page-stack {
    display: flex;
    flex-direction: column;
}

.page-section--title { order: 1; }
.page-section--fetch { order: 2; }
.page-section--ticket { order: 3; }
.page-section--loading { order: 4; }
.page-section--results { order: 5; }
.page-section--actions { order: 6; }

.placeholder-page {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 48px;
    text-align: center;
    color: #666;
}

.page-title {
    font-size: 28px;
    font-weight: 700;
    color: #111;
    margin-bottom: 20px;
}

.ticket-fetch-row {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
}

.ticket-fetch-input {
    flex: 1;
    max-width: 480px;
}

.ticket-card {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 16px;
}

.ticket-card-title {
    font-size: 18px;
    font-weight: 700;
    color: #111;
    margin-bottom: 12px;
}

.ticket-card-description {
    font-size: 15px;
    color: #444;
    line-height: 1.5;
    margin-bottom: 20px;
}

.btn-generate {
    background: #111 !important;
    color: #fff !important;
}

.loading-banner {
    background: #f5f5f5;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: #555;
    font-size: 14px;
    margin-bottom: 20px;
}

.results-panel {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

.results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    gap: 16px;
}

.results-title {
    font-size: 16px;
    font-weight: 700;
    color: #111;
}

.saved-path {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #666;
    font-size: 13px;
}

.test-case-card {
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.test-case-card:last-child {
    margin-bottom: 0;
}

.test-case-title {
    font-size: 15px;
    font-weight: 600;
    color: #222;
    flex: 1;
}

.test-case-expected {
    font-size: 14px;
    color: #666;
    margin-top: 8px;
}

.badge-functional {
    background: #e8f5e9;
    color: #2e7d32;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-edge-case {
    background: #fff3e0;
    color: #e65100;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-negative {
    background: #ffebee;
    color: #c62828;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-functional,
.badge-edge-case,
.badge-negative {
    display: inline-block;
    line-height: 1.4;
}

.action-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.action-bar .q-btn {
    text-transform: none;
}

.pr-url-input {
    flex: 1;
    max-width: 720px;
}

.pr-card {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 16px;
}

.pr-card-title {
    font-size: 18px;
    font-weight: 700;
    color: #111;
    margin-bottom: 10px;
}

.pr-card-stats {
    font-size: 14px;
    color: #666;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.pr-provider {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.review-comments-panel {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

.review-comments-title {
    font-size: 16px;
    font-weight: 700;
    color: #111;
    margin-bottom: 16px;
}

.review-comment-card {
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 16px 16px 16px 20px;
    margin-bottom: 12px;
    border-left-width: 4px;
    border-left-style: solid;
}

.review-comment-card:last-child {
    margin-bottom: 0;
}

.review-comment--high {
    border-left-color: #e53935;
}

.review-comment--medium {
    border-left-color: #fb8c00;
}

.review-comment--style {
    border-left-color: #78909c;
}

.review-comment-location {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.review-comment-text {
    font-size: 14px;
    color: #555;
    line-height: 1.5;
    margin-top: 8px;
}

.badge-severity-high {
    background: #ffebee;
    color: #c62828;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-severity-medium {
    background: #fff3e0;
    color: #e65100;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-severity-style {
    background: #eceff1;
    color: #546e7a;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 999px;
    white-space: nowrap;
}

.badge-severity-high,
.badge-severity-medium,
.badge-severity-style {
    display: inline-block;
    line-height: 1.4;
}

.integration-card {
    background: #ffffff;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

.integration-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}

.integration-title {
    font-size: 16px;
    font-weight: 700;
    color: #111;
}

.integration-row {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
    width: 100%;
}

.integration-row:last-child {
    margin-bottom: 0;
}

.integration-field {
    flex: 1;
    min-width: 0;
}

.integration-field--full {
    flex: 1;
    width: 100%;
}

.settings-save-row {
    margin-top: 8px;
}
"""
