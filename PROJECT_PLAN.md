# 🛡️ Full-Stack DevSecOps & Switchable Vulnerable Web App Project Plan

本ドキュメントは、**「Cloudflare Pages + Workers + D1 DB」** で動作するフルスタック動的Webアプリケーションの構築、環境変数による **「やられサイト（脆弱性実験）スイッチ」**、**「4大セキュリティツール（SAST / DAST / SCA / Secret Scan）を統括するフル DevSecOps CI/CD パイプライン」**、および **「独自ドメインによる本番ホスティング」** を実現する正式プロジェクト計画書です。

---

## 🎯 プロジェクトの目的と概要

1. **スイッチ型やられサイト（Vulnerable Mode Switch）付き動的Webアプリの構築**
   - ユーザー認証、メモ/掲示板API、データベース（Cloudflare D1 SQLite）を備えたモダンなフルスタックWebアプリ。
   - `VULNERABLE_MODE=true/false` の切り替えにより、SQLインジェクション、反射型XSS、機密情報漏洩、CORS誤設定などを意図的に発現・無効化可能。
2. **フル DevSecOps CI/CD パイプラインの構築**
   - コードの `push` 時、GitHub Actions の使い捨て環境内でアプリを起動し、以下の4大セキュリティ診断を完全自動で実行。
     - 🔍 **SAST (静的解析):** `Semgrep` (コード内の潜在的リスク検出)
     - 🔑 **Secret Scan (機密情報漏洩):** `Gitleaks` (APIキー・認証情報の直書き検出)
     - 📦 **SCA (ライブラリ監査):** `npm audit` / `Trivy` (依存パッケージの既知の脆弱性検出)
     - 🕷️ **DAST (動的スキャン):** `Katana` (クローラー) + `Nuclei` (動的脆弱性診断)
   - スキャン結果は GitHub Actions の **Step Summary** 画面に一元表示し、**Artifacts** としてZIP保存。
3. **Cloudflare Pages / Workers ＋ 独自ドメインでの本番運用**
   - CI/CD パイプライン通過後、自動で Cloudflare Pages へデプロイ。
   - 取得済みの Cloudflare 独自ドメインを紐付け、完全無料・スリープなし・HTTPS対応の本番環境として公開。

---

## 🏗️ システムアーキテクチャ & 技術スタック

```
[開発者] ── (git push) ──> [GitHub Repository]
                                 │
                                 ▼ (GitHub Actions 起動)
┌─────────────────────────────────────────────────────────────────┐
│                    🛡️ DevSecOps CI/CD Pipeline                  │
│                                                                 │
│  1. Secret Scan : Gitleaks (APIキー直書き検知)                   │
│  2. SAST        : Semgrep (ソースコード静的解析)                │
│  3. SCA         : npm audit / Trivy (ライブラリ監査)           │
│  4. DAST        : Katana (クローラー) + Nuclei (動的診断)       │
│                   ※使い捨て環境内で VULNERABLE_MODE=true 起動   │
│                                                                 │
│  📊 Summary Report を GitHub Actions 実行画面に自動出力        │
└─────────────────────────────────────────────────────────────────┘
                                 │ (スキャン完了 & 合格)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  🚀 Cloudflare Production Host                  │
│                                                                 │
│  - Frontend  : Cloudflare Pages (HTML5/CSS3/JS)                 │
│  - Backend   : Cloudflare Workers / Pages Functions            │
│  - Database  : Cloudflare D1 (SQLite)                          │
│  - Security  : Cloudflare WAF + DDoS Protection                 │
│  - Domain    : 独自ドメイン (https://your-domain.com)          │
└─────────────────────────────────────────────────────────────────┘
```

| レイヤー | 採用技術・ツール | 役割・説明 |
| :--- | :--- | :--- |
| **フロントエンド** | HTML5 / Vanilla CSS / JS | モダンなレスポンシブUI、認証画面、メモ管理画面 |
| **バックエンド/API** | Cloudflare Workers / Pages Functions | 超軽量・高速なサーバーレスAPI処理 |
| **データベース** | Cloudflare D1 (SQLite) | ユーザーデータ、メモ投稿データの永続化 |
| **SAST (静的解析)** | Semgrep | コード内のSQLiパターンやXSS、不安全な関数の検出 |
| **Secret Scan** | Gitleaks | `.env` やコード内の秘密鍵・APIキー誤コミット検出 |
| **SCA (ライブラリ監査)**| npm audit / Trivy | 依存パッケージの既知脆弱性 (CVE) 診断 |
| **DAST (動的診断)** | Katana + Nuclei | 起動中アプリに対する自動巡回＆動的脆弱性診断 |
| **ホスティング** | Cloudflare Pages + 独自ドメイン | 無料・スリープなし・HTTPS常時対応の本番基盤 |

---

## 📂 ディレクトリ構成（予定）

```text
githubpages/
├── .github/
│   └── workflows/
│       └── deploy.yml            # 4大セキュリティ統合 CI/CD ワークフロー
├── vulnerable_server.py          # CI/CDローカルテスト用 脆弱性発現サーバー
├── app.js                        # Cloudflare Workers / API ロジック
├── schema.sql                    # Cloudflare D1 テーブル定義 (SQL)
├── index.html                    # メインフロントエンド画面
├── style.css                     # デザインシステム・スタイル
├── script.js                     # フロントエンドインタラクション
├── wrangler.toml                 # Cloudflare Pages / D1 設定ファイル
├── PROJECT_PLAN.md               # プロジェクト計画書 (本ファイル)
└── README.md                     # プロジェクト概要ドキュメント
```

---

## 🧪 検証計画 (Verification Plan)

1. **ローカル ＆ CI/CD セキュリティ検証**
   - `VULNERABLE_MODE=true` 時に Semgrep、Gitleaks、Katana、Nuclei の4ツールすべてが正常に脆弱性を検知し、GitHub Actions の Step Summary 画面へ見やすいレポートとして出力されることを確認。
2. **安全モード機能の検証**
   - `VULNERABLE_MODE=false` 時に パラメータが適切にサニタイズされ、SQLプレースホルダーが使用されて脆弱性が無効化されることを確認。
3. **Cloudflare デプロイ ＆ 独自ドメイン疎通確認**
   - `wrangler-action` により Cloudflare Pages へ自動デプロイされ、指定した独自ドメイン（`https://...`）でスリープなし・HTTPSでレスポンスが返ることを確認。

---
*Created on 2026-07-21 for Antigravity Project Integration.*
