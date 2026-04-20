/* ──────────────────────────────────────
   에어캡 시장 단가 통합 모니터링 시스템
   JavaScript Logic
   ────────────────────────────────────── */

// 설정
const CONFIG = {
  // GitHub raw CSV URL
  CSV_URL: 'https://raw.githubusercontent.com/38o0264-ops/BubbleWrap_Monitor/main/price_history.csv',
  // 비밀번호
  PASSWORD: '10077',
  // 차트 색상
  COMPANY_COLORS: {
    '박스몰': '#3366ff',
    '비닐닷컴': '#ff6b35',
    '포장몰': '#00d68f',
    '달인 패키지': '#9d4edd'
  }
};

// 전역 상태
let appData = {
  rawData: [],
  processedData: [],
  latestDate: null,
  isLoggedIn: false
};

/* ── 초기화 ── */
document.addEventListener('DOMContentLoaded', () => {
  // 로그인창 기본 숨김 (깜빡임 방지)
  const loginOverlay = document.getElementById('login-overlay');
  loginOverlay.style.display = 'none';
  
  // 세션 복원 확인
  if (localStorage.getItem('aircap_session') === 'authenticated') {
    // 자동 로그인 - 로그인창 숨김 유지
    loginOverlay.classList.add('hidden');
    showLoading();
    loadData().then(() => {
      hideLoading();
      showDashboard();
    }).catch(err => {
      console.error('Data load error:', err);
      hideLoading();
      showDashboard();
    });
  } else {
    // 세션 없음 - 로그인창 표시
    loginOverlay.style.display = 'flex';
    initLogin();
  }
});

/* ── 로그인 처리 ── */
function initLogin() {
  const passwordInput = document.getElementById('app-password');
  const submitBtn = document.getElementById('submit-password');
  const errorMsg = document.getElementById('password-error');
  const loginOverlay = document.getElementById('login-overlay');
  
  // Enter 키 처리
  passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      checkPassword();
    }
  });
  
  // 버튼 클릭
  submitBtn.addEventListener('click', checkPassword);
  
  // SHA-256 해시 함수
  async function sha256(message) {
    const encoder = new TextEncoder();
    const data = encoder.encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  function checkPassword() {
    const input = passwordInput.value;
    
    if (input === CONFIG.PASSWORD) {
      // 로그인 성공
      errorMsg.classList.add('hidden');
      appData.isLoggedIn = true;
      
      // 세션 저장 (브라우저 닫기 전까지 유지)
      localStorage.setItem('aircap_session', 'authenticated');
      
      // 백그라운드에서 데이터 로딩 시작
      showLoading();
      loginOverlay.classList.add('hidden');
      
      // 데이터 로드 후 대시보드 표시
      loadData().then(() => {
        hideLoading();
        showDashboard();
      }).catch(err => {
        console.error('Data load error:', err);
        hideLoading();
        showDashboard();
        showError('데이터를 불러오는 중 오류가 발생했습니다.');
      });
    } else {
      // 로그인 실패
      errorMsg.classList.remove('hidden');
      passwordInput.value = '';
      passwordInput.focus();
      
      // 흔들림 애니메이션
      const modal = document.querySelector('.password-modal');
      modal.style.animation = 'shake 0.5s';
      setTimeout(() => {
        modal.style.animation = '';
      }, 500);
    }
  }
}

/* ── 데이터 로딩 ── */
async function loadData() {
  try {
    const response = await fetch(CONFIG.CSV_URL + '?t=' + Date.now()); // 캐시 방지
    const csvText = await response.text();
    
    // CSV 파싱
    const results = Papa.parse(csvText, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    });
    
    appData.rawData = results.data;
    
    // 데이터 처리
    processData();
    
    return true;
  } catch (error) {
    console.error('Error loading CSV:', error);
    throw error;
  }
}

/* ── 데이터 처리 ── */
function processData() {
  // 날짜 파싱
  appData.rawData.forEach(row => {
    if (row.date) {
      row.dateObj = new Date(row.date);
    }
  });
  
  // 최신 날짜 찾기
  const dates = appData.rawData.map(row => row.dateObj).filter(d => d);
  appData.latestDate = dates.length > 0 ? new Date(Math.max(...dates)) : null;
  
  // 메트릭 계산 (20×30 환산)
  appData.processedData = appData.rawData.map(row => {
    const unitPrice = parseFloat(row.unit_price) || 0;
    const qtyPerBox = parseFloat(row.qty_per_box) || 1;
    const shipping = parseFloat(row.shipping_per_box) || 0;
    const width = parseFloat(row.width) || 1;
    const height = parseFloat(row.height) || 1;
    const vatStatus = row.vat_status || '미포함';
    
    // 박스당 가격
    const boxPrice = unitPrice * qtyPerBox;
    
    // 배송비+VAT포함 단가
    let realCost = unitPrice + (shipping / qtyPerBox);
    if (vatStatus === '미포함') {
      realCost *= 1.1;
    }
    
    // 20×30 환산단가
    const convertedPrice = (realCost / (width * height)) * 600;
    
    return {
      ...row,
      boxPrice: Math.round(boxPrice),
      realCost: Math.round(realCost),
      convertedPrice: Math.round(convertedPrice)
    };
  });
}

/* ── 대시보드 표시 ── */
function showDashboard() {
  const dashboard = document.getElementById('main-dashboard');
  dashboard.classList.remove('hidden');
  
  // 메트릭 업데이트
  updateMetrics();
  
  // 테이블 생성
  createDataTable();
  
  // 차트 생성
  createChart();
  
  // 이력 테이블 생성
  createHistoryTable();
  
  // 새로고침 버튼 이벤트
  document.getElementById('refresh-btn').addEventListener('click', () => {
    showLoading();
    loadData().then(() => {
      hideLoading();
      updateMetrics();
      createDataTable();
      createChart();
      createHistoryTable();
    });
  });
}

/* ── 메트릭 업데이트 ── */
async function updateMetrics() {
  // 최신 조사시간 - last_update.txt에서 읽어옴
  const lastUpdateEl = document.getElementById('last-update-time');
  try {
    const response = await fetch('https://raw.githubusercontent.com/38o0264-ops/BubbleWrap_Monitor/main/last_update.txt?t=' + Date.now());
    const updateTime = await response.text();
    if (updateTime && updateTime.trim()) {
      lastUpdateEl.textContent = updateTime.trim();
    } else if (appData.latestDate) {
      const formatted = appData.latestDate.toLocaleDateString('ko-KR');
      lastUpdateEl.textContent = formatted;
    } else {
      lastUpdateEl.textContent = '수집 기록 없음';
    }
  } catch (e) {
    // fallback to date from data
    if (appData.latestDate) {
      const formatted = appData.latestDate.toLocaleDateString('ko-KR');
      lastUpdateEl.textContent = formatted;
    } else {
      lastUpdateEl.textContent = '수집 기록 없음';
    }
  }
  
  // 최저 단가 (최신 날짜 기준)
  const latestData = appData.processedData.filter(row => {
    if (!row.dateObj || !appData.latestDate) return false;
    return row.dateObj.toDateString() === appData.latestDate.toDateString();
  });
  
  if (latestData.length > 0) {
    const cheapest = latestData.reduce((min, row) => 
      row.convertedPrice < min.convertedPrice ? row : min
    );
    
    document.getElementById('cheapest-price').textContent = 
      cheapest.convertedPrice.toLocaleString() + '원';
    document.getElementById('cheapest-company').textContent = 
      `${cheapest.company} · ${cheapest.product}`;
  }
}

/* ── 데이터 테이블 생성 ── */
function createDataTable() {
  const container = document.getElementById('data-table-container');
  
  // 최신 날짜 데이터 필터링
  const latestData = appData.processedData.filter(row => {
    if (!row.dateObj || !appData.latestDate) return false;
    return row.dateObj.toDateString() === appData.latestDate.toDateString();
  });
  
  // 정렬 (박스몰 우선, 환산단가 오름차순)
  latestData.sort((a, b) => {
    const aIsBoxmall = a.company.includes('박스몰');
    const bIsBoxmall = b.company.includes('박스몰');
    if (aIsBoxmall && !bIsBoxmall) return -1;
    if (!aIsBoxmall && bIsBoxmall) return 1;
    return a.convertedPrice - b.convertedPrice;
  });
  
  // 최저가 찾기
  const minPrice = latestData.length > 0 
    ? Math.min(...latestData.map(d => d.convertedPrice))
    : 0;
  
  let html = `
    <table>
      <thead>
        <tr>
          <th>상태</th>
          <th>회사명</th>
          <th>상품명</th>
          <th>사용범위</th>
          <th>판매여부</th>
          <th>규격 (cm)</th>
          <th style="text-align: right;">단가</th>
          <th style="text-align: right;">입수량</th>
          <th style="text-align: right;">배송비</th>
          <th style="text-align: right;">박스당 가격</th>
          <th style="text-align: right;">부가세</th>
          <th style="text-align: right;">배송비+VAT포함 단가</th>
          <th style="text-align: right; color: #2E7D32;">20*30로 환산단가</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  latestData.forEach(row => {
    const isCheapest = row.convertedPrice === minPrice;
    const bgColor = isCheapest ? '#E8F5E9' : 'transparent';
    const isSoldOut = row.availability !== '판매중';
    const rowClass = isSoldOut ? 'sold-out-row' : '';
    
    const shippingDisplay = row.shipping_per_box === 0 
      ? '무료배송' 
      : row.shipping_per_box.toLocaleString() + '원';
    
    const availabilityHtml = isSoldOut 
      ? '<span style="color: #ff4b4b; font-weight: 500;">품절</span>'
      : `<a href="${row.product_url || '#'}" target="_blank">판매중 🔗</a>`;
    
    // 상태 표시 (수집=녹색, 수동=회색, 오류=빨강)
    let statusClass = 'status-neutral';
    let statusText = '⚪';
    if (row.status === '수집') {
      statusClass = 'status-success';
      statusText = '●';
    } else if (row.status === '수동') {
      statusClass = 'status-manual';
      statusText = '●';
    } else if (row.status === '오류') {
      statusClass = 'status-error';
      statusText = '●';
    }
    
    html += `
      <tr class="${rowClass}" style="background-color: ${bgColor};">
        <td style="text-align: center;" class="${statusClass}">${statusText}</td>
        <td>${row.company}</td>
        <td>${row.product}</td>
        <td>${row.usage_scope || '범용'}</td>
        <td>${availabilityHtml}</td>
        <td style="color: #666;">${row.width}x${row.height}</td>
        <td style="text-align: right;">${Math.round(row.unit_price).toLocaleString()}원</td>
        <td style="text-align: right;">${Math.round(row.qty_per_box).toLocaleString()}매</td>
        <td style="text-align: right;">${shippingDisplay}</td>
        <td style="text-align: right;">${row.boxPrice.toLocaleString()}원</td>
        <td style="text-align: right;">${row.vat_status || '미포함'}</td>
        <td style="text-align: right;">${row.realCost.toLocaleString()}원</td>
        <td style="text-align: right; font-weight: 700;">${row.convertedPrice.toLocaleString()}원</td>
      </tr>
    `;
  });
  
  html += '</tbody></table>';
  container.innerHTML = html;
}

/* ── 차트 생성 ── */
function createChart() {
  const chartContainer = document.getElementById('price-chart');
  const chartInfo = document.getElementById('chart-info');
  
  // 날짜가 2개 이상인지 확인
  const uniqueDates = [...new Set(appData.processedData.map(row => 
    row.dateObj ? row.dateObj.toDateString() : null
  ))].filter(d => d);
  
  if (uniqueDates.length < 2) {
    chartContainer.classList.add('hidden');
    chartInfo.classList.remove('hidden');
    return;
  }
  
  chartContainer.classList.remove('hidden');
  chartInfo.classList.add('hidden');
  
  // 차트 데이터 준비 - 각 회사별 날짜별 최저가만 표시
  const chartData = [];
  const companies = [...new Set(appData.processedData.map(row => row.company))];
  
  companies.forEach(company => {
    const companyData = appData.processedData.filter(row => row.company === company);
    
    // 날짜별로 그룹화하여 각 날짜의 최저 convertedPrice 선택
    const dateGroups = {};
    companyData.forEach(row => {
      const dateKey = row.dateObj.toDateString();
      if (!dateGroups[dateKey] || row.convertedPrice < dateGroups[dateKey].convertedPrice) {
        dateGroups[dateKey] = row;
      }
    });
    
    // 날짜 순으로 정렬
    const cheapestPerDate = Object.values(dateGroups).sort((a, b) => a.dateObj - b.dateObj);
    
    chartData.push({
      x: cheapestPerDate.map(row => row.dateObj),
      y: cheapestPerDate.map(row => row.convertedPrice),
      mode: 'lines+markers',
      name: company,
      line: {
        color: CONFIG.COMPANY_COLORS[company] || '#888',
        width: 2
      },
      marker: {
        size: 8
      },
      hovertemplate: 
        '%{x|%Y-%m-%d}<br>' +
        `${company}<br>` +
        '20×30 환산단가: %{y:,}원<extra></extra>'
    });
  });
  
  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(26, 26, 46, 0.8)',
    font: {
      family: 'Noto Sans KR, sans-serif',
      size: 13,
      color: '#fff'
    },
    legend: {
      orientation: 'h',
      yanchor: 'bottom',
      y: 1.02,
      xanchor: 'right',
      x: 1,
      bgcolor: 'rgba(0,0,0,0.3)',
      bordercolor: 'rgba(255,255,255,0.1)',
      borderwidth: 1
    },
    margin: { l: 60, r: 20, t: 60, b: 60 },
    hovermode: 'x unified',
    xaxis: {
      gridcolor: 'rgba(255,255,255,0.05)',
      tickformat: '%y.%m.%d',
      title: '조사 날짜'
    },
    yaxis: {
      gridcolor: 'rgba(255,255,255,0.05)',
      title: '20×30 환산단가 (원)',
      title_standoff: 10
    },
    height: 450
  };
  
  const config = {
    responsive: true,
    displayModeBar: false
  };
  
  Plotly.newPlot('price-chart', chartData, layout, config);
}

/* ── 이력 테이블 생성 ── */
function createHistoryTable() {
  const container = document.getElementById('history-table-container');
  
  // 전체 데이터 정렬 (날짜 내림차순)
  const sortedData = [...appData.processedData].sort((a, b) => 
    b.dateObj - a.dateObj
  );
  
  let html = `
    <table>
      <thead>
        <tr>
          <th>날짜</th>
          <th>회사명</th>
          <th>상품명</th>
          <th>🔗</th>
          <th>판매여부</th>
          <th>가로</th>
          <th>세로</th>
          <th style="text-align: right;">단가</th>
          <th style="text-align: right;">입수량</th>
          <th style="text-align: right;">배송비</th>
          <th style="text-align: right;">박스당 가격</th>
          <th style="text-align: right;">배송비+VAT포함 단가</th>
          <th style="text-align: right;">20×30 환산단가</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  sortedData.forEach(row => {
    const dateStr = row.dateObj 
      ? row.dateObj.toLocaleDateString('ko-KR') 
      : '-';
    
    const linkHtml = row.product_url 
      ? `<a href="${row.product_url}" target="_blank">🔗</a>`
      : '-';
    
    html += `
      <tr>
        <td>${dateStr}</td>
        <td>${row.company}</td>
        <td>${row.product}</td>
        <td>${linkHtml}</td>
        <td>${row.availability || '판매중'}</td>
        <td>${row.width}</td>
        <td>${row.height}</td>
        <td style="text-align: right;">${Math.round(row.unit_price).toLocaleString()}</td>
        <td style="text-align: right;">${Math.round(row.qty_per_box).toLocaleString()}</td>
        <td style="text-align: right;">${Math.round(row.shipping_per_box).toLocaleString()}</td>
        <td style="text-align: right;">${row.boxPrice.toLocaleString()}</td>
        <td style="text-align: right;">${row.realCost.toLocaleString()}</td>
        <td style="text-align: right;">${row.convertedPrice.toLocaleString()}</td>
      </tr>
    `;
  });
  
  html += '</tbody></table>';
  container.innerHTML = html;
}

/* ── 로딩 표시 ── */
function showLoading() {
  document.getElementById('loading-indicator').classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-indicator').classList.add('hidden');
}

/* ── 에러 표시 ── */
function showError(message) {
  alert(message);
}

/* ── CSS 애니메이션 추가 ── */
const style = document.createElement('style');
style.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
  }
`;
document.head.appendChild(style);
