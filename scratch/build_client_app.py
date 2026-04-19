import sys

def build_client_app():
    # 1. Get the perfect check_password from our latest aircap_final_boss.txt
    with open(r'c:\Users\Art Yoon\Downloads\Antigravity\BubbleWrap_Monitor\deploy_aircap\aircap_final_boss.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    start = text.find('def check_password():')
    end = text.find('st.set_page_config(')
    perfect_check_password = text[start:end].strip()

    # 2. Read the original app.py
    with open(r'c:\Users\Art Yoon\Downloads\Antigravity\BubbleWrap_Monitor\app.py', 'r', encoding='utf-8') as f:
        app_text = f.read()

    # 3. Replace the check_password logic
    app_start = app_text.find('def check_password():')
    app_end = app_text.find('return True\n', app_start) + len('return True\n')
    app_text = app_text[:app_start] + perfect_check_password + '\n\n' + app_text[app_end:]

    # 4. Remove crawler imports and logic
    lines = app_text.split('\n')
    new_lines = []
    skip_auto = False
    skip_btn = False
    skip_manual = False

    for line in lines:
        if 'import crawler' in line:
            continue
        
        # Skip auto update function
        if 'def trigger_auto_update():' in line:
            skip_auto = True
        if skip_auto and line.strip() == '# ──────────────────────────────────────':
            skip_auto = False
        if skip_auto:
            continue

        # Remove auto update calls
        if 'trigger_auto_update()' in line and 'def ' not in line:
            continue
            
        # Skip real-time update button block
        if 'if st.button("🔄 실시간 가격 업데이트' in line:
            skip_btn = True
        if skip_btn and 'st.rerun()' in line:
            skip_btn = False
            continue
        if skip_btn:
            continue

        # Skip manual update block
        if 'with st.expander("📝 데이터 수동 업데이트' in line:
            skip_manual = True
        if skip_manual and line.strip() == '# ──────────────────────────────────────':
            # Actually manual update might go till the end of the script or the next big section, let's just break since it's the last section.
            break
        if skip_manual:
            continue
        
        new_lines.append(line)

    final_text = '\n'.join(new_lines)
    with open(r'c:\Users\Art Yoon\Downloads\Antigravity\BubbleWrap_Monitor\deploy_aircap\aircap_final_boss.txt', 'w', encoding='utf-8') as f:
        f.write(final_text)

if __name__ == '__main__':
    build_client_app()
    print("Dashboard cleaned and deployed.")
