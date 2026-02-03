# 📚 自動化學術論文下載器 (AutoRef)
這是一個基於 Python 與 Selenium (undetected-chromedriver) 的自動化工具，專門設計用於批量下載學術論文。它具備繞過 Cloudflare 驗證、擬人化操作以及自動備份列印的功能。

✨ 核心功能
🛡️ 強大的抗偵測機制：使用 undetected_chromedriver，有效降低被識別為機器人的風險。

☁️ Cloudflare 自動過盾：內建智慧邏輯，能偵測並處理 Cloudflare 的 Turnstile 驗證（包含 Iframe 切換與擬人化點擊）。

🖱️ 擬人化操作：使用 ActionChains 模擬滑鼠移動、懸停與隨機延遲點擊，避免機械式操作。

🧩 模組化網站支援：

IEEE Xplore：自動構造下載連結。

PubMed / NCBI：自動跳轉至 PMC 免費全文。

ResearchGate：自動尋找並點擊隱藏的下載按鈕。

通用模式：掃描頁面上的 Meta Tag 或 PDF 連結。

🖨️ 智慧備份 (WebPrint)：若無法下載原始 PDF，會自動使用 Chrome CDP 協議將網頁「列印」為 PDF 保存，確保不空手而歸。

🔧 穩定性優化：自動偵測 Chrome 版本，並具備進程清理機制，防止記憶體洩漏。

🛠️ 環境需求
作業系統：Windows (程式碼針對 Windows 路徑優化)

瀏覽器：Google Chrome (最新版)

程式語言：Python 3.8+

安裝依賴套件
請在終端機 (Terminal/PowerShell) 執行以下指令安裝所需套件：

Bash
pip install undetected-chromedriver selenium
(注意：程式碼中未依賴 webdriver_manager，因為 undetected-chromedriver 會自動處理驅動程式)

🚀 使用方法
1. 準備下載清單
在腳本同一個目錄下，建立一個名為 list.txt 的檔案。 每行放一個網址，支援 Markdown 格式或純網址。

list.txt 範例：

Plaintext
https://pubmed.ncbi.nlm.nih.gov/12345678/
[論文標題] https://www.researchgate.net/publication/12345
(IEEE文章) https://ieeexplore.ieee.org/document/9876543
2. 執行腳本
執行你的 Python 檔案（例如 main.py）：

Bash
python main.py
3. 查看結果
程式執行後會自動建立以下檔案與目錄：

downloaded_docs/：存放下載成功的 PDF 檔案。檔名會自動加入序號與論文標題。

failed_urls.txt：若有失敗的任務，會記錄在此檔案中方便重試。

⚙️ 程式邏輯說明
1. 驅動程式初始化 (setup_driver)
採用 Factory Pattern，每次啟動前產生全新的 ChromeOptions，避免 RuntimeError。

優先嘗試自動匹配 Chrome 版本，若失敗則退回至指定的穩定版本 (如 144)。

2. 過盾邏輯 (bypass_cloudflare)
偵測頁面原始碼是否包含 security check 或 challenges.cloudflare.com。

若偵測到，程式會嘗試切換至驗證碼所在的 iframe。

使用 human_click 函數模擬真人滑鼠軌跡進行點擊。

3. 下載策略 (process_single_url)
程式會依序執行以下步驟：

導航：依據網址類型（IEEE/PubMed/其他）選擇不同的進入策略。

偵測：等待頁面載入並嘗試過盾。

抓取：透過 find_pdf_element 尋找下載按鈕或 Meta Tag。

驗證：監控下載資料夾，確認是否有新檔案 (.pdf) 產生。

備份：若上述失敗，呼叫 save_webpage_as_pdf 進行網頁列印。

⚠️ 常見問題排除
Error 1020 (Access Denied)：

這是 IP 被網站防火牆封鎖。

解法：請更換 IP（例如連接手機熱點），或暫停一段時間再執行。

Cloudflare 無限迴圈：

若程式點擊後不斷重新驗證，代表瀏覽器指紋被懷疑。

解法：手動介入點擊瀏覽器視窗，或更換乾淨的 IP。

WinError 6 (控制代碼無效)：

這是 Python 關閉進程時的偶發錯誤，不影響下載結果，可忽略。

📝 免責聲明
本工具僅供學術研究與個人檔案備份使用。請勿用於大規模爬取或違反目標網站服務條款 (ToS) 之行為。使用者需自行承擔使用風險。

版本：v2.0 (Optimized Architecture) 更新日期：2026-02-02
