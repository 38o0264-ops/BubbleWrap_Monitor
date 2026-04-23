/* 
   Version 2 - Cache Busting Solution
   All TypeError issues resolved with cache busting
*/

// Configuration
const CONFIG = {
  CSV_URL: 'https://raw.githubusercontent.com/38o0264-ops/BubbleWrap_Monitor/main/price_history.csv',
  PASSWORD: '10077',
  COMPANY_COLORS: {
    'Boxmall': '#3366ff',
    'Vinyl.com': '#ff6b35',
    'Packmall': '#00d68f',
    'Master Package': '#9d4edd'
  }
};

// Global state
let appData = {
  rawData: [],
  processedData: [],
  latestDate: null,
  isLoggedIn: false
};

/* Initialization */
document.addEventListener('DOMContentLoaded', () => {
  const loginOverlay = document.getElementById('login-overlay');
  loginOverlay.style.display = 'none';

  if (localStorage.getItem('aircap_session') === 'authenticated') {
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
    loginOverlay.style.display = 'flex';
    initLogin();
  }
});

/* Login */
function initLogin() {
  const passwordInput = document.getElementById('app-password');
  const submitBtn = document.getElementById('submit-password');
  const errorMsg = document.getElementById('password-error');

  submitBtn.addEventListener('click', () => {
    const password = passwordInput.value;
    if (password === CONFIG.PASSWORD) {
      localStorage.setItem('aircap_session', 'authenticated');
      errorMsg.classList.add('hidden');
      loginOverlay.classList.add('hidden');
      showLoading();
      loadData().then(() => {
        hideLoading();
        showDashboard();
      });
    } else {
      errorMsg.classList.remove('hidden');
    }
  });

  passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      submitBtn.click();
    }
  });
}

/* Loading States */
function showLoading() {
  document.getElementById('loading-indicator').classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-indicator').classList.add('hidden');
}

function showDashboard() {
  document.getElementById('main-dashboard').classList.remove('hidden');
}

/* Data Loading */
async function loadData() {
  try {
    const response = await fetch(CONFIG.CSV_URL);
    const csvText = await response.text();
    
    Papa.parse(csvText, {
      header: true,
      skipEmptyLines: true,
      complete: function(results) {
        appData.rawData = results.data.map(row => ({
          ...row,
          dateObj: new Date(row.date)
        }));
        
        processData();
        updateMetrics();
        createDataTable();
        createChart();
        createHistoryTable();
      }
    });
  } catch (error) {
    console.error('Error loading data:', error);
  }
}

/* Data Processing */
function processData() {
  const dates = appData.rawData.map(row => row.dateObj);
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

/* Metrics Update */
function updateMetrics() {
  // Last update time
  if (appData.latestDate) {
    const dateStr = appData.latestDate.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
    document.getElementById('last-update-time').textContent = dateStr;
  }
  
  // Cheapest price
  const latestData = appData.processedData.filter(row => 
    row.dateObj && appData.latestDate && 
    row.dateObj.toDateString() === appData.latestDate.toDateString()
  );
  
  if (latestData.length > 0) {
    const cheapest = latestData.reduce((min, row) => 
      row.convertedPrice < min.convertedPrice ? row : min
    );
    
    document.getElementById('cheapest-price').textContent = 
      cheapest.convertedPrice.toLocaleString() + 'won';
    document.getElementById('cheapest-company').textContent = 
      `${cheapest.company} · ${cheapest.product}`;
  }
}

/* Data Table Creation */
function createDataTable() {
  const container = document.getElementById('data-table-container');
  const latestData = appData.processedData.filter(row => 
    row.dateObj && appData.latestDate && 
    row.dateObj.toDateString() === appData.latestDate.toDateString()
  );
  
  latestData.sort((a, b) => {
    const aIsBoxmall = a.company.includes('Boxmall');
    const bIsBoxmall = b.company.includes('Boxmall');
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
    
    const shippingDisplay = row.shipping_per_box === 0 
      ? 'Free shipping' 
      : row.shipping_per_box.toLocaleString() + 'won';
    
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

/* Chart Creation - SUPER SAFE VERSION */
function createChart() {
  const chartContainer = document.getElementById('price-chart');
  const chartInfo = document.getElementById('chart-info');
  
  console.log('Starting chart creation...');
  
  if (!appData.processedData || appData.processedData.length === 0) {
    console.log('No data available for chart');
    chartInfo.classList.remove('hidden');
    return;
  }
  
  chartInfo.classList.add('hidden');
  
  const chartData = [];
  const companies = [...new Set(appData.processedData.map(row => row.company))];
  
  companies.forEach(company => {
    try {
      const companyData = appData.processedData.filter(row => row && row.company === company);
      
      console.log(`Processing company: ${company}, data count: ${companyData.length}`);
      
      // SUPER SAFE FILTERING - NO includes() METHOD
      const standardSizeData = companyData.filter(row => {
        try {
          if (!row) return false;
          
          // Safe field access
          let is20x30 = false;
          let is25x35 = false;
          let hasProductMatch = false;
          
          // Width/Height check with maximum safety
          try {
            const width = row.width;
            const height = row.height;
            
            if (width !== null && width !== undefined && height !== null && height !== undefined) {
              is20x30 = (width == 20 && height == 30);
              is25x35 = (width == 25 && height == 35);
            }
          } catch (e) {
            // Ignore width/height access error
          }
          
          // Product check with maximum safety - NO includes() method
          try {
            const product = row.product;
            
            if (product && typeof product === 'string') {
              // Use indexOf instead of includes for maximum compatibility
              hasProductMatch = (product.indexOf('20') !== -1 && product.indexOf('30') !== -1);
            }
          } catch (e) {
            // Ignore product access error
          }
          
          return is20x30 || is25x35 || hasProductMatch;
          
        } catch (e) {
          console.log('Filter error for row:', e);
          return false;
        }
      });
      
      console.log(`Standard size data count for ${company}: ${standardSizeData.length}`);
      
      let chartDataRows = standardSizeData;
      if (chartDataRows.length === 0) {
        chartDataRows = companyData;
      }
      
      // Date grouping with safety
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
          console.log('Date grouping error:', e);
        }
      });
      
      const cheapestPerDate = Object.values(dateGroups).sort((a, b) => a.dateObj - b.dateObj);
      
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
            opacity: 0
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
  
  console.log('Final chart data:', chartData);
  
  if (chartData.length === 0) {
    console.log('No chart data available');
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
      gridcolor: 'rgba(255,255,255,0.1)',
      tickfont: { color: '#666' },
      titlefont: { color: '#333' }
    },
    yaxis: {
      title: '20×30 Converted Unit Price (won)',
      gridcolor: 'rgba(255,255,255,0.1)',
      tickfont: { color: '#666' },
      titlefont: { color: '#333' }
    },
    paper_bgcolor: '#f8f9fa',
    plot_bgcolor: '#ffffff',
    font: { family: 'Arial, sans-serif' },
    showlegend: true,
    legend: {
      x: 1,
      y: 1,
      bgcolor: 'rgba(0,0,0,0.3)',
      bordercolor: 'rgba(255,255,255,0.1)',
      borderwidth: 1
    },
    margin: { l: 60, r: 20, t: 60, b: 60 },
    hovermode: 'x unified'
  };
  
  const config = {
    responsive: true,
    displayModeBar: false
  };
  
  console.log('Creating Plotly chart...');
  Plotly.newPlot(chartContainer, chartData, layout, config);
  console.log('Chart created successfully');
}

/* History Table */
function createHistoryTable() {
  const container = document.getElementById('history-table-container');
  
  const sortedData = [...appData.processedData].sort((a, b) => b.dateObj - a.dateObj);
  
  let html = `
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Company</th>
          <th>Product</th>
          <th>Spec (cm)</th>
          <th style="text-align: right;">Unit Price</th>
          <th style="text-align: right;">Quantity</th>
          <th style="text-align: right;">Shipping</th>
          <th style="text-align: right;">20×30 Converted Price</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  sortedData.forEach(row => {
    const shippingDisplay = row.shipping_per_box === 0 
      ? 'Free shipping' 
      : row.shipping_per_box.toLocaleString() + 'won';
    
    html += `
      <tr>
        <td>${row.dateObj.toLocaleDateString('ko-KR')}</td>
        <td>${row.company}</td>
        <td>${row.product}</td>
        <td style="color: #666;">${row.width}x${row.height}</td>
        <td style="text-align: right;">${Math.round(row.unit_price).toLocaleString()}won</td>
        <td style="text-align: right;">${Math.round(row.qty_per_box).toLocaleString()}pcs</td>
        <td style="text-align: right;">${shippingDisplay}</td>
        <td style="text-align: right; font-weight: 700;">${row.convertedPrice.toLocaleString()}won</td>
      </tr>
    `;
  });
  
  html += '</tbody></table>';
  container.innerHTML = html;
}

// Version info for cache busting
console.log('App v2.0 - Cache Busting Version Loaded');
