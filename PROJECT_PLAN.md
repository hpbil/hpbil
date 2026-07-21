# 🛡️ Full-Stack DevSecOps & Switchable Vulnerable Web App Project Plan

本ドキュメントは、**「Cloudflare Pages (フロント) + Workers (API) + D1 DB」** で動作するフルスタック動的Webアプリケーションの構築、環境変数による **「やられサイト（脆弱性実験）スイッチ」**、**「4大セキュリティツール（SAST / DAST / SCA / Secret Scan）を統括するフル DevSecOps CI/CD パイプライン」**、**「CORS学習のためのドメイン分離構成」**、および **「Cloudflare Access (Zero Trust) による本番全域保護」** を実現する完全仕様書 兼 プロジェクト計画書です。

---

## 🎯 プロジェクトの目的と概要

1. **多機能「スイッチ型やられサイト」付き動的Webアプリの構築**
   - ユーザー登録・ログイン（JWT/Cookie認証）、メモ投稿・管理機能、データベース（Cloudflare D1 SQLite）を備えたモダンWebアプリ。
   - `VULNERABLE_MODE=true/false` の切り替えにより、主要な脆弱性（SQLi, XSS, 認証不備, 情報漏洩, **CORS設定ミス**, IDOR/BOLA）を網羅的に発現・無効化。
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
4. **ドメイン分離構成 (CORS & クロスドメイン認証の学習環境)**
   - フロント（`https://your-domain.com`）と API バックエンド（`https://api.your-domain.com`）をあえて分離。
   - プリフライト (`OPTIONS`) リクエスト、`Access-Control-Allow-Origin` の誤設定、`SameSite=None; Secure` Cookie の取り扱いを深く学べる実戦的構成。
5. **Cloudflare Access (Zero Trust) による本番ドメイン全域保護 ＆ 独自ドメイン運用**
   - 本番の Cloudflare Pages / Workers 全域の手前に **Cloudflare Access**（50ユーザー無料枠）を挟み、自分以外の外部からのアクセスを完全遮断。
   - 外部攻撃のリスクがゼロとなるため、本番の Cloudflare Pages 上でも安全に `VULNERABLE_MODE=true`（やられサイト機能）を稼働させてクラウド実地での脆弱性動作検証が可能。

---

## 🔍 検証・設計上のブラインドスポット対策 (Blind Spots & Solutions)

### 1. Cloudflare Access 認証と CI/CD DAST スキャンの競合回避
- **課題:** 本番ドメインに Cloudflare Access 認証を設定すると、CI/CD 上の Nuclei スキャンも認証プロンプトでブロックされる。
- **対策:** CI/CD 上での DAST スキャン（Katana & Nuclei）は、使い捨て環境内の `localhost:8080` のみに向けて実行し、Access 認証によるブロックの影響を受けずに安全かつ確実にスキャンを完結させる。

### 2. Cloudflare D1 (SQLite) の制約と SQLi の適合
- **課題:** D1 (SQLite) は複数ステートメント (Multi-statement query: `; DROP TABLE...`) の同時実行がドライバーレベルで制限される。
- **対策:** 認証回避 (`OR 1=1`) や データ抽出 (`UNION SELECT`) など、D1/SQLite の制約内で確実に動作・検証できるリアルな SQLi パターンに特化。

### 3. リポジトリの公開範囲 (Public) とダミーキーの扱い
- **リポジトリ状態:** ポートフォリオ/実績として GitHub 上で Public（公開）のまま運用。
- **誤警告防止策:** テスト用ダミーキーには `DUMMY_API_KEY_FOR_TESTING_ONLY` 等の明示的なテスト専用命名規則を適用し、`.gitleaksignore` を配置して GitHub や Gitleaks の誤検知アラートを防止。

---

## 🏛️ アーキテクチャ選定理由 ＆ 役割分担 (Decision Rationale)

### ❓ なぜ Cloudflare 内蔵 CI/CD ではなく GitHub Actions を採用するのか？

Cloudflare Pages にも標準で自動ビルド・デプロイ機能（CI/CD）が用意されていますが、本プロジェクトではあえて **GitHub Actions を CI/CD 司令塔** として採用しています。その理由は以下の通りです：

1. **高度なセキュリティツール（Katana / Nuclei / Gitleaks等）の実行環境確保**
   - Cloudflare Pages の内蔵 CI/CD は標準的な Web ビルド（`npm run build` 等）のみに対応しています。
   - 一方、GitHub Actions では完全な Linux 仮想環境が提供されるため、Go製の Katana / Nuclei のインストール、テスト用ローカルサーバーの起動、動的セキュリティスキャンを自由自在に組み合わせることが可能です。
2. **「デプロイ前ブロック（Shift Left Security）」の関門（ゲートキーパー）化**
   - Cloudflare Pages 内蔵 CI/CD では `push` されると無条件で即時デプロイされてしまいます。
   - GitHub Actions を間に挟むことで、**「4大セキュリティスキャンを通過（合格）したコードのみを Cloudflare Pages へ安全に送出する」** という DevSecOps の厳格な品質ゲートを構築できます。

---

## 📊 GitHub と Cloudflare の機能別役割分担表

| 担当領域 | 🐙 GitHub (開発・検証工場) | 🟠 Cloudflare (本番配信基盤) |
| :--- | :--- | :--- |
| **コード管理** | **100% 担当**<br>リポジトリ管理、バージョン制御 | 担当しない |
| **セキュリティ診断** | **100% 担当**<br>Semgrep / Gitleaks / Katana & Nuclei の実行 | 担当しない |
| **CI/CD 司令塔** | **100% 担当**<br>使い捨て環境でのテスト＆合否判定＆デプロイ指示 | 担当しない |
| **Webサービス配信** | 担当しない | **100% 担当**<br>Cloudflare Pages (`your-domain.com`) |
| **バックエンド API** | 担当しない | **100% 担当**<br>Cloudflare Workers (`api.your-domain.com`) |
| **データベース** | 担当しない | **100% 担当**<br>Cloudflare D1 (SQLite) でデータ永続化 |
| **ドメイン ＆ セキュリティ** | 担当しない | **100% 担当**<br>独自ドメイン設定、HTTPS暗号化、**Cloudflare Access (Zero Trust)** |

---

## 🏗️ システムアーキテクチャ & 技術スタック

```
[開発者] ── (git push) ──> [GitHub Repository (Public)]
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
│           🚀 Cloudflare Production Host (Zero Trust)            │
│                                                                 │
│  - Access Guard: Cloudflare Access (Zero Trust 全域認証保護)    │
│  - Frontend    : Cloudflare Pages (your-domain.com)             │
│  - Backend API : Cloudflare Workers (api.your-domain.com)       │
│  - Database    : Cloudflare D1 (SQLite)                        │
│  - Mode        : 本番上でも VULNERABLE_MODE=true が安全稼働可能  │
│  - Learn Cors  : OPTIONS プリフライト / CORS誤設定 / Cookie検証 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 組み込み脆弱性バリエーション（網羅型）

`VULNERABLE_MODE=true` 時に意図的に有効化される脆弱性リスト：

1. **SQL インジェクション (SQLi):** D1/SQLite互換の生SQL結合（認証回避 `OR 1=1` / データ抽出 `UNION SELECT`）。
2. **クロスサイトスクリプティング (XSS):** メモ本文や検索キーワードのHTMLサニタイズ処理省略。
3. **認証 / JWTの脆弱性:** JWT署名検証スキップ（`alg: none` 許容）、Cookie の `HttpOnly` / `SameSite` フラグ未設定。
4. **機密情報の露出 (Information Disclosure):** `/.env` や `/api/debug` でのダミーシークレット露出。
5. **CORS設定ミス ＆ セキュリティヘッダー欠落:** `Access-Control-Allow-Origin: *` + `Credentials: true` の不安全組み合わせおよび CSP/X-Frame-Options の欠落。
6. **認可不備 / IDOR (BOLA):** 他人のメモIDを直接指定することで閲覧・改ざん可能なアクセス制御欠落。

---

## 📂 ディレクトリ構成

```text
githubpages/
├── .github/
│   └── workflows/
│       └── deploy.yml            # 4大セキュリティ統合 & BLOCKトグル付き CI/CD
├── .gitleaksignore               # Gitleaks誤検知防止フィルター
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
3. **CORS ＆ ドメイン分離動作検証**
   - フロント（`your-domain.com`）から API（`api.your-domain.com`）へのクロスドメイン通信が正常に行われ、`VULNERABLE_MODE` に応じて CORS ヘッダーが安全/不安全に変化することを確認。
4. **Cloudflare Access 保護下の本番動作確認**
   - Cloudflare Access 認証をパスした自分だけが本番環境にアクセスでき、本番上でも `VULNERABLE_MODE=true`（やられサイト機能）が安全に検証・体験できることを確認。

---
*Updated on 2026-07-21 with Blindspots Resolution (DAST vs Access, D1 SQLi Model, CORS & Domain Separation).*
