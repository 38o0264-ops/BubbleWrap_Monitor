/* Korean AirCap Monitoring App - FINAL SOLUTION */
/* Cache Busting: 202404229999 */

const CONFIG = {
  CSV_URL: 'https://raw.githubusercontent.com/38o0264-ops/BubbleWrap_Monitor/main/price_history.csv',
  PASSWORD: '10077',
  COMPANY_COLORS: {
    'Boxmall': '#3366ff',
    'Vinyl.com': '#ff6b35',
    'Packmall': '#00d68f',
    'General': '#9e9e9e'
  }
};

const appData = {
  rawData: [],
  processedData: [],
  latestDate: null,
  isAuthenticated: false
};

function initializeApp() {
  console.log('Initializing Korean AirCap App...');
  setupEventListeners();
  checkAuthentication();
}

function setupEventListeners() {
  const submitBtn = document.getElementById('submit-password');
  const passwordInput = document.getElementById('app-password');
  const passwordForm = document.getElementById('password-form');
  
  if (submitBtn && passwordInput && passwordForm) {
    submitBtn.addEventListener('click', handlePasswordSubmit);
    passwordInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handlePasswordSubmit();
      }
    });
    passwordForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handlePasswordSubmit();
    });
  }
}

function checkAuthentication() {
  const sessionAuth = sessionStorage.getItem('aircap_authenticated');
  if (sessionAuth === 'true') {
    appData.isAuthenticated = true;
    showMainDashboard();
    loadData();
  } else {
    showLoginModal();
  }
}

function handlePasswordSubmit() {
  const passwordInput = document.getElementById('app-password');
  const errorElement = document.getElementById('password-error');
  const password = passwordInput.value.trim();
  
  if (password === CONFIG.PASSWORD) {
    appData.isAuthenticated = true;
    sessionStorage.setItem('aircap_authenticated', 'true');
    hideLoginModal();
    showMainDashboard();
    loadData();
  } else {
    errorElement.classList.remove('hidden');
    passwordInput.value = '';
    passwordInput.focus();
  }
}

function showLoginModal() {
  const loginOverlay = document.getElementById('login-overlay');
  const mainDashboard = document.getElementById('main-dashboard');
  const loadingIndicator = document.getElementById('loading-indicator');
  
  if (loginOverlay) loginOverlay.classList.remove('hidden');
  if (mainDashboard) mainDashboard.classList.add('hidden');
  if (loadingIndicator) loadingIndicator.classList.add('hidden');
}

function hideLoginModal() {
  const loginOverlay = document.getElementById('login-overlay');
  const errorElement = document.getElementById('password-error');
  const passwordInput = document.getElementById('app-password');
  
  if (loginOverlay) loginOverlay.classList.add('hidden');
  if (errorElement) errorElement.classList.add('hidden');
  if (passwordInput) passwordInput.value = '';
}

function showMainDashboard() {
  const mainDashboard = document.getElementById('main-dashboard');
  const loadingIndicator = document.getElementById('loading-indicator');
  
  if (mainDashboard) mainDashboard.classList.remove('hidden');
  if (loadingIndicator) loadingIndicator.classList.remove('hidden');
}

function showLoadingIndicator() {
  const loadingIndicator = document.getElementById('loading-indicator');
  if (loadingIndicator) loadingIndicator.classList.remove('hidden');
}

function hideLoadingIndicator() {
  const loadingIndicator = document.getElementById('loading-indicator');
  if (loadingIndicator) loadingIndicator.classList.add('hidden');
}

function loadData() {
  showLoadingIndicator();
  
  Papa.parse(CONFIG.CSV_URL, {
    download: true,
    header: true,
    complete: function(results) {
      appData.rawData = results.data.filter(row => row.date && row.company && row.product);
      processData();
      updateMetrics();
      createDataTable();
      createChart();
      createHistoryTable();
      hideLoadingIndicator();
    },
    error: function(error) {
      console.error('CSV loading error:', error);
      hideLoadingIndicator();
      alert('CSV Loading error');
    }
  });
}

function processData() {
  appData.rawData.forEach(row => {
    if (row.date) {
      try {
        row.dateObj = new Date(row.date);
        if (isNaN(row.dateObj.getTime())) {
          const parts = row.date.split('-');
          if (parts.length === 3) {
            row.dateObj = new Date(parts[0], parts[1] - 1, parts[2]);
          }
        }
      } catch (e) {
        console.error('Date parsing error:', e);
      }
    }
  });
  
  const dates = appData.rawData
    .map(row => row.dateObj)
    .filter(date => date && !isNaN(date.getTime()));
  
  appData.latestDate = dates.length > 0 ? new Date(Math.max(...dates)) : null;
  
  appData.processedData = appData.rawData.map(row => {
    const unitPrice = parseFloat(row.unit_price) || 0;
    const qtyPerBox = parseFloat(row.qty_per_box) || 1;
    const shipping = parseFloat(row.shipping_per_box) || 0;
    const width = parseFloat(row.width) || 1;
    const height = parseFloat(row.height) || 1;
    const vatStatus = row.vat_status || 'Not included';
    
    const boxPrice = unitPrice * qtyPerBox;
    let realCost = unitPrice + (shipping / qtyPerBox);
    if (vatStatus === 'Not included') {
      realCost *= 1.1;
    }
    
    const convertedPrice = (realCost / (width * height)) * 600;
    
    return {
      ...row,
      boxPrice: Math.round(boxPrice),
      realCost: Math.round(realCost),
      convertedPrice: Math.round(convertedPrice)
    };
  });
}

function updateMetrics() {
  const lastUpdateElement = document.getElementById('last-update-time');
  const cheapestPriceElement = document.getElementById('cheapest-price');
  const cheapestCompanyElement = document.getElementById('cheapest-company');
  
  if (appData.latestDate) {
    const formattedDate = appData.latestDate.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    if (lastUpdateElement) lastUpdateElement.textContent = formattedDate;
  }
  
  const latestData = appData.processedData.filter(row => 
    row.dateObj && appData.latestDate && 
    row.dateObj.toDateString() === appData.latestDate.toDateString()
  );
  
  if (latestData.length > 0) {
    const cheapest = latestData.reduce((min, row) => 
      row.convertedPrice < min.convertedPrice ? row : min
    );
    
    if (cheapestPriceElement) cheapestPriceElement.textContent = 
      cheapest.convertedPrice.toLocaleString() + 'won';
    if (cheapestCompanyElement) cheapestCompanyElement.textContent = 
      `${cheapest.company} · ${cheapest.product}`;
  }
}

function createDataTable() {
  const container = document.getElementById('data-table-container');
  if (!container) return;
  
  const latestData = appData.processedData.filter(row => 
    row.dateObj && appData.latestDate && 
    row.dateObj.toDateString() === appData.latestDate.toDateString()
  );
  
  latestData.sort((a, b) => {
    const aIsBoxmall = a.company.indexOf('Boxmall') !== -1;
    const bIsBoxmall = b.company.indexOf('Boxmall') !== -1;
    if (aIsBoxmall && !bIsBoxmall) return -1;
    if (!aIsBoxmall && bIsBoxmall) return 1;
    return a.convertedPrice - b.convertedPrice;
  });
  
  const minPrice = latestData.length > 0 
    ? Math.min(...latestData.map(d => d.convertedPrice))
    : 0;
  
  let html = `
    <table>
      <thead>
        <tr>
          <th>Company Name</th>
          <th>Product Name</th>
          <th>Usage Range</th>
          <th>Sale Status</th>
          <th>Spec (cm)</th>
          <th style="text-align: right;">Unit Price</th>
          <th style="text-align: right;">Quantity</th>
          <th style="text-align: right;">Shipping</th>
          <th style="text-align: right;">Box Price</th>
          <th style="text-align: right;">VAT</th>
          <th style="text-align: right;">Shipping+VAT Unit Price</th>
          <th style="text-align: right; color: #2E7D32;">20*30 Converted Unit Price</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  latestData.forEach(row => {
    const isCheapest = row.convertedPrice === minPrice;
    const bgColor = isCheapest ? '#E8F5E9' : 'transparent';
    const isSoldOut = row.availability !== 'For sale';
    const rowClass = isSoldOut ? 'sold-out-row' : '';
    
    const shippingDisplay = shipping === 0 ? 
      '<span style="color: #2E7D32;">Free shipping</span>' : 
      shipping.toLocaleString() + 'won';
    
    const availabilityHtml = isSoldOut 
      ? '<span style="color: #ff4b4b; font-weight: 500;">Sold out</span>'
      : `<a href="${row.product_url || '#'}" target="_blank">For sale</a>`;
    
    html += `
      <tr class="${rowClass}" style="background-color: ${bgColor};">
        <td>${row.company}</td>
        <td>${row.product}</td>
        <td>${row.usage_scope || 'General'}</td>
        <td>${availabilityHtml}</td>
        <td style="color: #666;">${row.width}x${row.height}</td>
        <td style="text-align: right;">${Math.round(row.unit_price).toLocaleString()}won</td>
        <td style="text-align: right;">${Math.round(row.qty_per_box).toLocaleString()}pcs</td>
        <td style="text-align: right;">${shippingDisplay}</td>
        <td style="text-align: right;">${row.boxPrice.toLocaleString()}won</td>
        <td style="text-align: right;">${row.vat_status || 'Not included'}</td>
        <td style="text-align: right;">${row.realCost.toLocaleString()}won</td>
        <td style="text-align: right; font-weight: 700;">${row.convertedPrice.toLocaleString()}won</td>
      </tr>
    `;
  });
  
  html += '</tbody></table>';
  container.innerHTML = html;
}

function createChart() {
  const chartContainer = document.getElementById('price-chart');
  const chartInfo = document.getElementById('chart-info');
  
  if (!chartContainer) return;
  
  chartInfo.classList.add('hidden');
  
  const chartData = [];
  const companies = [...new Set(appData.processedData.map(row => row.company))];
  
  companies.forEach(company => {
    try {
      const companyData = appData.processedData.filter(row => row && row.company === company);
      
      const standardSizeData = companyData.filter(row => {
        if (!row || !row.width || !row.height) return false;
        
        let is20x30 = false;
        let is25x35 = false;
        let hasProductMatch = false;
        
        try {
          const width = parseFloat(row.width);
          const height = parseFloat(row.height);
          
          if (!isNaN(width) && !isNaN(height)) {
            is20x30 = (width == 20 && height == 30);
            is25x35 = (width == 25 && height == 35);
          }
        } catch (e) {
          // Ignore width/height access error
        }
        
        try {
          const product = row.product;
          
          if (product && typeof product === 'string') {
            hasProductMatch = (product.indexOf('20') !== -1 && product.indexOf('30') !== -1);
          }
        } catch (e) {
          // Ignore product access error
        }
        
        return is20x30 || is25x35 || hasProductMatch;
        
      });
      
      let chartDataRows = standardSizeData;
      if (chartDataRows.length === 0) {
        chartDataRows = companyData;
      }
      
      const dateGroups = {};
      chartDataRows.forEach(row => {
        try {
          if (row && row.dateObj) {
            const dateKey = row.dateObj.toDateString();
            if (!dateGroups[dateKey] || row.convertedPrice < dateGroups[dateKey].convertedPrice) {
              dateGroups[dateKey] = row;
            }
          }
        } catch (e) {
          // Ignore date grouping error
        }
      });
      
      const cheapestPerDate = Object.values(dateGroups).sort((a, b) => 
        new Date(a.date) - new Date(b.date)
      );
      
      if (cheapestPerDate.length > 0) {
        chartData.push({
          x: cheapestPerDate.map(row => row.dateObj),
          y: cheapestPerDate.map(row => row.convertedPrice),
          mode: 'lines',
          name: company,
          line: {
            color: CONFIG.COMPANY_COLORS[company] || '#888',
            width: 2
          },
          marker: {
            size: 0,
          },
          hovertemplate: 
            '%{x|%Y-%m-%d}<br>' +
            `${company}<br>` +
            '20x30 Converted Unit Price: %{y:,}won<extra></extra>'
        });
      }
      
    } catch (e) {
      console.log(`Error processing company ${company}:`, e);
    }
  });
  
  if (chartData.length === 0) {
    chartInfo.classList.remove('hidden');
    return;
  }
  
  const layout = {
    title: {
      text: '20×30 Converted Unit Price Trend',
      font: { size: 16 }
    },
    xaxis: {
      title: 'Date',
      type: 'date',
      gridcolor: 'rgba(0,0,0,0.1)'
    },
    yaxis: {
      title: 'Price (won)',
      gridcolor: 'rgba(0,0,0,0.1)'
    },
    plot_bgcolor: 'rgba(248,249,250,0.8)',
    paper_bgcolor: 'white',
    font: {
      family: 'Noto Sans KR, sans-serif'
    },
    showlegend: true,
    legend: {
      x: 0,
      y: 1,
      bgcolor: 'rgba(0,0,0,0.3)',
      bordercolor: 'rgba(255,255,255,0.1)',
      borderwidth: 1
    },
    margin: { l: 60, r: 20, t: 60, b: 60 }
  };
  
  const config = {
    responsive: true,
    displayModeBar: false
  };
  
  Plotly.newPlot(chartContainer, chartData, layout, config);
}

function createHistoryTable() {
  const container = document.getElementById('history-table-container');
  if (!container) return;
  
  const sortedData = [...appData.processedData].sort((a, b) => {
    if (!a.dateObj || !b.dateObj) return 0;
    return b.dateObj - a.dateObj;
  });
  
  let html = `
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Company</th>
          <th>Product</th>
          <th>Spec</th>
          <th style="text-align: right;">Unit Price</th>
          <th style="text-align: right;">Converted Price</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  sortedData.forEach(row => {
    if (!row.dateObj) return;
    
    html += `
      <tr>
        <td>${row.dateObj.toLocaleDateString('ko-KR')}</td>
        <td>${row.company}</td>
        <td>${row.product}</td>
        <td style="color: #666;">${row.width}x${row.height}</td>
        <td style="text-align: right;">${Math.round(row.unit_price).toLocaleString()}won</td>
        <td style="text-align: right; font-weight: 600;">${row.convertedPrice.toLocaleString()}won</td>
      </tr>
    `;
  });
  
  html += '</tbody></table>';
  container.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', initializeApp);
