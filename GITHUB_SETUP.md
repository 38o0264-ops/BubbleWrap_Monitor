# GitHub Pages 배포 가이드

## 1. GitHub Repository 생성

1. https://github.com/new 에 접속
2. Repository name: `BubbleWrap_Monitor` 입력
3. Public 선택 (Private은 GitHub Pages Pro 필요)
4. "Create repository" 클릭

## 2. 파일 업로드

아래 파일들을 GitHub에 업로드합니다:

```
BubbleWrap_Monitor/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── app.js
├── crawler.py
├── run_gh_crawl.py
├── price_history.csv (초기 데이터)
├── last_update.txt
└── .github/
    └── workflows/
        └── crawl.yml
```

### 업로드 방법:

**방법 A: GitHub 웹 인터페이스**
1. GitHub repo 페이지에서 "Add file" → "Upload files" 클릭
2. 파일들을 드래그 앤 드롭
3. Commit changes

**방법 B: Git 명령어**
```bash
cd C:\Users\Art Yoon\Downloads\Windsurf\BubbleWrap_Monitor

# Git 초기화
git init
git add .
git commit -m "Initial commit"

# GitHub repo 연결 (YOUR_USERNAME을 실제 GitHub username으로 변경)
git remote add origin https://github.com/38o0264-ops/BubbleWrap_Monitor.git
git branch -M main
git push -u origin main
```

## 3. GitHub Pages 활성화

1. GitHub repo → Settings → Pages 이동
2. Source: "Deploy from a branch" 선택
3. Branch: "main" / "(root)" 선택
4. Save 클릭

## 4. app.js 설정 변경

`js/app.js` 파일에서 GitHub URL을 본인의 것으로 변경:

```javascript
const CONFIG = {
  // GitHub raw CSV URL (본인의 username으로 변경!)
  CSV_URL: 'https://raw.githubusercontent.com/38o0264-ops/BubbleWrap_Monitor/main/price_history.csv',
  PASSWORD: '10077',
  // ...
};
```

## 5. 카페24 업로드 (선택사항)

카페24에 `aircap` 폴더를 생성하고 아래 파일들만 업로드:

```
aircap/
├── index.html
├── css/
│   └── style.css
└── js/
    └── app.js
```

⚠️ **중요**: `js/app.js`의 CSV_URL은 GitHub raw URL을 그대로 사용합니다.

## 6. 접속 주소

- **GitHub Pages**: `https://38o0264-ops.github.io/BubbleWrap_Monitor/`
- **카페24**: `https://ayodele.co.kr/aircap/`

## 7. 자동 크롤링 확인

GitHub Actions 탭에서 워크플로우 실행 상태 확인:
1. Actions 탭 클릭
2. "24/7 AirCap Price Crawler" 워크플로우 확인
3. 1시간마다 자동 실행되거나 "Run workflow" 버튼으로 수동 실행

## 문제 해결

### CORS 오류 발생 시
GitHub raw URL은 기본적으로 CORS 헤더를 제공합니다. 만약 문제가 발생하면:
1. GitHub Pages로 직접 배포 권장
2. 또는 https://corsproxy.io/ 같은 프록시 서비스 사용 (개발용)

### 데이터가 안 불러와질 때
1. `price_history.csv`가 GitHub에 push되었는지 확인
2. 브라우저 콘솔(F12)에서 오류 메시지 확인
3. CSV URL이 정확한지 확인 (대소문자, 공백 등)

## 비밀번호 변경

`js/app.js`에서 PASSWORD 값 수정:
```javascript
PASSWORD: '원하는비밀번호',
```
