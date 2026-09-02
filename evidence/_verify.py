import time, re, json
from playwright.sync_api import sync_playwright

URL = "https://ryoseiimai.github.io/ai-pachinko-maker/"
SHOTS = "/Users/ryoseiworld/dev/2026-09-02-ai-pachinko-maker/evidence/shots"
BAN = ["設定", "出玉", "還元", "勝てる"]

def check_viewport(p, w, h, tag):
    result = {"viewport": f"{w}x{h}"}
    errors = []
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": w, "height": h})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(800)

    # 1. 分析パネルが画面内に見えるか
    panel = page.locator("#analysisPanel")
    box = panel.bounding_box()
    in_view_1 = bool(box) and box["y"] < h and box["y"] + box["height"] > 0 and box["y"] >= 0
    # 厳密に「viewport内に見える」= top < h and bottom > 0
    visible_1 = bool(box) and box["y"] < h and (box["y"] + box["height"]) > 0
    result["1_analysis_panel_visible"] = visible_1
    page.screenshot(path=f"{SHOTS}/final_{tag}_01_initial.png")

    # 2. 別のIPで診断 x3、毎回IPが変わるか
    titles = []
    for i in range(4):
        t = page.locator("#analysisBody .tag").first.inner_text()
        titles.append(t)
        if i < 3:
            page.locator("#btnRandom").click()
            page.wait_for_timeout(500)
    changed_all = all(titles[i] != titles[i+1] for i in range(3))
    result["2_random_ip_changes"] = changed_all
    result["2_titles"] = titles
    page.screenshot(path=f"{SHOTS}/final_{tag}_02_after_random.png")

    # 3. あなたの推しは？ でカード一覧へスクロール / カードクリックで分析更新+画面内へ戻る
    before_scroll = page.evaluate("window.scrollY")
    page.locator("#btnPick").click()
    page.wait_for_timeout(700)
    after_scroll = page.evaluate("window.scrollY")
    scrolled = after_scroll != before_scroll or page.locator("#cardGrid").bounding_box() is not None
    grid_box = page.locator("#cardGrid").bounding_box()
    grid_in_view = bool(grid_box) and grid_box["y"] < h and (grid_box["y"] + grid_box["height"]) > 0
    result["3a_scroll_to_cards"] = grid_in_view
    page.screenshot(path=f"{SHOTS}/final_{tag}_03a_pick_scroll.png")

    prev_title = page.locator("#analysisBody .tag").first.inner_text()
    cards = page.locator("#cardGrid .card")
    target_idx = min(2, cards.count()-1)
    cards.nth(target_idx).click()
    page.wait_for_timeout(800)
    new_title = page.locator("#analysisBody .tag").first.inner_text()
    panel_box2 = page.locator("#analysisPanel").bounding_box()
    panel_in_view2 = bool(panel_box2) and panel_box2["y"] < h and (panel_box2["y"] + panel_box2["height"]) > 0
    result["3b_card_click_updates_and_scrolls_back"] = (new_title != prev_title) and panel_in_view2
    result["3b_titles"] = [prev_title, new_title]
    page.screenshot(path=f"{SHOTS}/final_{tag}_03b_card_click.png")

    # 4. Xシェア -> 新規タブで x.com/intent/post
    intent_url = None
    try:
        with page.context.expect_page(timeout=5000) as new_page_info:
            page.locator("#btnShare").click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded", timeout=5000)
        intent_url = new_page.url
        new_page.close()
    except Exception as e:
        intent_url = f"ERROR: {e}"
    result["4_share_intent_url"] = intent_url

    # 5. 経営モードタブで4件編成
    page.locator('.tab-btn[data-tab="keiei"]').click()
    page.wait_for_timeout(500)
    pick_children = page.locator("#keieiPickList > *")
    n = pick_children.count()
    clicked = 0
    for i in range(n):
        if clicked >= 4:
            break
        el = pick_children.nth(i)
        try:
            el.click(timeout=1500)
            clicked += 1
            page.wait_for_timeout(400)
        except Exception:
            continue
    page.wait_for_timeout(500)
    sales_text = page.locator("#keieiSales").inner_text() if page.locator("#keieiSales").count() else ""
    warn_text = page.locator("#keieiWarn").inner_text() if page.locator("#keieiWarn").count() else ""
    result["5_keiei_clicked_count"] = clicked
    result["5_sales_text"] = sales_text
    result["5_warn_text"] = warn_text
    page.screenshot(path=f"{SHOTS}/final_{tag}_05_keiei.png", full_page=True)

    # 6. コンソールエラー0、横スクロール無し、禁止語チェック
    result["6_console_errors"] = errors
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    client_width = page.evaluate("document.documentElement.clientWidth")
    result["6_horizontal_scroll"] = scroll_width > client_width + 2
    result["6_scroll_width_vs_client"] = [scroll_width, client_width]

    body_text = page.evaluate("document.body.innerText")
    # 免責文抽出（class disclaimer や 注記等含む可能性、まず全文からdisclaimer行を除外する簡易策）
    disclaimer_texts = page.locator(".disclaimer, .note, .caution, footer").all_inner_texts()
    disclaimer_joined = "\n".join(disclaimer_texts)
    ban_hits = {}
    for word in BAN:
        all_positions = [m.start() for m in re.finditer(re.escape(word), body_text)]
        in_disclaimer = [m.start() for m in re.finditer(re.escape(word), disclaimer_joined)]
        outside_count = len(all_positions) - len(in_disclaimer)
        ban_hits[word] = {"total": len(all_positions), "in_disclaimer": len(in_disclaimer), "outside_estimate": outside_count}
    result["6_ban_words"] = ban_hits

    browser.close()
    return result

with sync_playwright() as p:
    r_mobile = check_viewport(p, 390, 844, "mobile")
    r_desktop = check_viewport(p, 1280, 720, "desktop")

print(json.dumps({"mobile": r_mobile, "desktop": r_desktop}, ensure_ascii=False, indent=2))
