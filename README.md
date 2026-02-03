# 📄 AutoRef

這是一個基於 Python 的自動化論文下載工具。它利用 `undetected_chromedriver` 和 `Selenium` 來模擬真人操作，能夠繞過 Cloudflare 驗證（如 ResearchGate、PubMed），並自動將學術文獻下載為 PDF。

若無法直接下載 PDF，程式具備「網頁列印 (WebPrint)」的備援機制，確保能保存網頁內容。

## 🚀 主要特色 (Key Features)

* **🛡️ 強大的抗偵測機制**：
    * 使用 `undetected_chromedriver` 避開 WebDriver 指紋偵測。
    * 內建 `human_click` 函數，使用 `ActionChains` 模擬人類滑鼠的「移動 -> 懸停 -> 點擊」軌跡。
* **🧠 智慧型 Cloudflare 繞過**：
    * 自動偵測 "Verify you are human" 或 "Security check"。
    * 支援切換 `Iframe` 點擊隱藏的驗證勾選框。
* **🔄 自動版本修復**：
    * 啟動時自動偵測 Chrome 版本。若自動匹配失敗，會自動切換至強制版本 (v144) 模式，解決 `SessionNotCreatedException` 錯誤。
* **🎯 針對性網站優化**：
    * **IEEE Xplore**: 自動轉換為 Stamp URL 直接下載。
    * **PubMed**: 自動跳轉至 PMC 免費全文。
    * **ResearchGate**: 自動尋找並點擊隱藏的下載按鈕。
* **🖨️ 雙重備份機制**：
    * 優先嘗試下載原始 PDF。
    * 若下載失敗，自動使用`Chrome CDP`協議進行「無頭列印」，將網頁存為 PDF。

## 🛠️ 安裝需求 (Requirements)

確保你的電腦已安裝 **Google Chrome** 瀏覽器。

### 1. 安裝 Python 套件
請在終端機`(Terminal / PowerShell)`執行以下指令：

```Python
pip install undetected-chromedriver selenium webdriver-manager
```
## 📂 檔案結構 (Project Structure)

請確保你的資料夾結構如下：
```
Project_Folder/
│
├── main.py              # 主程式腳本 (你的 Python 檔案)
├── list.txt             # 輸入檔案：要下載的論文連結清單
├── downloaded_docs/     # 輸出資料夾：下載好的 PDF 會存在這裡
└── failed_urls.txt      # 記錄檔：下載失敗的連結會自動寫入此處
```
## 📖 使用說明 (Usage)
### 1. 準備連結清單
在腳本同級目錄下建立`list.txt`，並將目標網址貼上，一行一個：
```
[https://pubmed.ncbi.nlm.nih.gov/example1/](https://pubmed.ncbi.nlm.nih.gov/example1/)
[https://www.researchgate.net/publication/example2](https://www.researchgate.net/publication/example2)
[https://ieeexplore.ieee.org/document/example3](https://ieeexplore.ieee.org/document/example3)
```
### 2.執行過程
* 程式會自動啟動 Chrome 視窗（為了過盾，請勿手動關閉視窗）。
* Cloudflare 驗證：若遇到驗證，程式會嘗試自動點擊。若自動點擊失敗，程式會等待人工介入（你也可以手動點一下勾選框幫助它）。
* 下載完成：檔案會依照 [序號]_[標題].pdf 格式儲存於`downloaded_docs`資料夾。
## ⚙️ 核心邏輯解析
### 1. 驅動程式初始化 (Driver Setup)
為了避免`RuntimeError: you cannot reuse the ChromeOptions object`，程式採用了工廠模式`get_chrome_options()`。每次重新嘗試啟動`Driver`時，都會生成全新的`Options`物件。
### 2. 擬人化點擊 (Human Click)
不使用傳統的 element.click()，而是使用動作鏈：

```Python
ActionChains(driver).move_to_element(element).pause(random).click().perform()
```
這能有效降低被判定為機器人的機率。
### 3. Iframe 切換
Cloudflare 的驗證按鈕通常藏在`iframe`中。程式內建邏輯會自動搜尋`challenges.cloudflare.com`的框架並切換進去點擊，點擊完後自動切回主文件。

## ❓ 常見問題 (Troubleshooting)
* Q: 程式啟動時報錯 SessionNotCreatedException？ A: 程式內建了自動修復機制。它會先嘗試自動匹配版本，失敗後會自動重試並指定相容版本。若仍失敗，請更新你的 Google Chrome 至最新版。
* Q: 下載的 PDF 只有網頁截圖？ A: 這是「WebPrint」功能。當原始 PDF 下載失敗（例如該論文需要付費，或按鈕被隱藏），程式會將當前看到的網頁內容列印下來，確保你不會空手而歸。
* Q: 遇到 Cloudflare 無限迴圈怎麼辦？ A: 雖然程式有自動過盾邏輯，但若 IP 信譽過低可能無法通過。此時請手動點擊瀏覽器上的驗證框，程式偵測到頁面跳轉後會自動繼續執行。

## ⚠️ 免責聲明
本工具僅供學術研究與個人學習使用。請遵守目標網站的 robots.txt 規範與使用條款，切勿用於大規模惡意爬取或商業用途。
