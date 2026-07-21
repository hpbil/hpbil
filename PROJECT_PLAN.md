# 🛡️ Full-Stack DevSecOps & Switchable Vulnerable Web App Project Plan

本ドキュメントは、**「Cloudflare Pages + Workers + D1 DB」** で動作するフルスタック動的Webアプリケーションの構築、環境変数による **「やられサイト（脆弱性実験）スイッチ」**、**「4大セキュリティツール（SAST / DAST / SCA / Secret Scan）を統括するフル DevSecOps CI/CD パイプライン」**、および **「独自ドメインによる本番ホスティング」** を実現する詳細仕様書 兼 プロジェクト計画書です。

---

## 🎯 プロジェクトの目的と概要

1. **多機能「スイッチ型やられサイト」付き動的Webアプリの構築**
   - ユーザー登録・ログイン（JWT/Cookie認証）、メモ投稿・管理機能、データベース（Cloudflare D1 SQLite）を備えたモダンWebアプリ。
   - `VULNERABLE_MODE=true/false` の切り替えにより、主要な脆弱性（SQLi, XSS, 認証不備, 情報漏洩, CORS誤設定, IDOR/BOLA）を網羅的に発現・無効化。
2. **ダッシュボード一体型モダンUI**
   - ヘッダーにセキュリティ状態（`VULNERABLE` / `SECURE`）のステータスインジケーターを配置。
   - 各脆弱性をワンクリックで再現・テストできる「検証パネル」を搭載した直感的な開発者向けインターフェース。
3. **フル DevSecOps CI/CD パイプラインの構築**
   - コードの `push` 時、GitHub Actions の使い捨て環境内でアプリを起動し、以下の4大セキュリティ診断を完全自動で実行。
     - 🔍 **SAST (静的解析):** `Semgrep` (コード内の潜在的リスク・SQLi/XSSパターン検出)
     - 🔑 **Secret Scan (機密情報漏洩):** `Gitleaks` (APIキー・認証情報の直書き検出)
     - 📦 **SCA (ライブラリ監査):** `npm audit` / `Trivy` (依存パッケージの既知の脆弱性検出)
     - 🕷️ **DAST (動的スキャン):** `Katana` (クローラー) + `Nuclei` (動的脆弱性診断)
   - デフォルトは通過（Warnモード）だが、`BLOCK_ON_HIGH=true` のトグルスイッチで危険度High以上の検出時に自動デプロイをブロック可能。
4. **Cloudflare Pages / Workers ＋ 独自ドメインでの本番運用**
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
│  📊 Summary Report を GITHUB_STEP_SUMMARY に自動出力           │
│  🎛️ BLOCK_ON_HIGH トグルで High/Critical 検出時に自動失敗設定  │
└─────────────────────────────────────────────────────────────────┘
                                 │ (スキャン完了 & 合格)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  🚀 Cloudflare Production Host                  │
│                                                                 │
│  - Frontend  : Cloudflare Pages (ダッシュボード一体型モダンUI)   │
│  - Backend   : Cloudflare Workers / Pages Functions            │
│  - Database  : Cloudflare D1 (SQLite)                          │
│  - Security  : Cloudflare WAF + DDoS Protection                 │
│  - Domain    : 独自ドメイン (https://your-domain.com)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 組み込み脆弱性バリエーション（網羅型）

`VULNERABLE_MODE=true` 時に意図的に有効化される脆弱性リスト：

1. **SQL インジェクション (SQLi):** プレースホルダー非使用の生SQL結合（ユーザー検索・ログイン時）。
2. **クロスサイトスクリプティング (XSS):** メモ本文や検索キーワードのHTMLサニタイズ処理省略。
3. **認証 / JWTの脆弱性:** JWT署名検証スキップ（`alg: none` 許容）、Cookie の `HttpOnly` / `SameSite` フラグ未設定。
4. **機密情報の露出 (Information Disclosure):** `/.env` や `/api/debug` でのダミーシークレット露出。
5. **CORS設定ミス ＆ セキュリティヘッダー欠落:** `Access-Control-Allow-Origin: *` および CSP/X-Frame-Options の欠落。
6. **認可不備 / IDOR (BOLA):** 他人のメモIDを直接指定することで閲覧・改ざん可能なアクセス制御欠落。

---

## 📂 ディレクトリ構成

```text
githubpages/
├── .github/
│   └── workflows/
│       └── deploy.yml            # 4大セキュリティ統合 & BLOCKトグル付き CI/CD
├── vulnerable_server.py          # CI/CDローカルテスト用 脆弱性発現Python/Nodeサーバー
├── app.js                        # Cloudflare Workers / API ロジック (VULNERABLE_MODE対応)
├── schema.sql                    # Cloudflare D1 テーブル定義 (users, notes)
├── index.html                    # ステータス表示ランプ & 脆弱性検証パネル付きメインUI
├── style.css                     # モダンCSS / グラスモルフィズムデザイン
├── script.js                     # フロントエンドインタラクション & 検証パネル動作
├── wrangler.toml                 # Cloudflare Pages / D1 設定ファイル
├── PROJECT_PLAN.md               # プロジェクト計画書・仕様書 (本ファイル)
└── README.md                     # プロジェクト概要ドキュメント
```

---

## 🧪 検証計画 (Verification Plan)

1. **ローカル ＆ CI/CD 4大セキュリティ検証**
   - `VULNERABLE_MODE=true` 時に Semgrep、Gitleaks、Katana、Nuclei の4ツールすべてが正常に脆弱性を検知し、GitHub Actions の Step Summary 画面へ詳細レポートとして出力されることを確認。
2. **ブロック機能 (BLOCK_ON_HIGH) の検証**
   - `BLOCK_ON_HIGH=true` 設定時に、High/Critical な脆弱性が検出された際にCI/CDパイプラインが自動で失敗（デプロイストップ）することを確認。
3. **安全モード機能の検証**
   - `VULNERABLE_MODE=false` 時に パラメータがサニタイズされ、プレースホルダーSQLが使用されて全脆弱性が無効化されることを確認。
4. **Cloudflare デプロイ ＆ 独自ドメイン疎通確認**
   - `wrangler-action` により Cloudflare Pages へ自動デプロイされ、指定した独自ドメイン（`https://...`）でスリープなし・HTTPSで動的機能が正しく動作することを確認。

---
*Updated on 2026-07-21 via /grill-me detail alignment for Antigravity Integration.*
