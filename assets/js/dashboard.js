// Company Reputation Tracker - Dashboard JavaScript

// Dashboard data will be loaded from JSON files generated from the database
let dashboardData = null;

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', function() {
  console.log('Dashboard initialization started');
  
  // Get the base URL for the site
  const baseUrl = window.location.pathname.split('/').slice(0, -1).join('/') || '';
  console.log('Base URL:', baseUrl);
  
  // Fetch dashboard data from JSON file
  // Use relative path for GitHub Pages
  const dataUrl = 'assets/data/dashboard_data.json';
  console.log('Fetching data from:', dataUrl);
  
  fetch(dataUrl)
    .then(response => {
      console.log('Response status:', response.status);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Data loaded successfully:', data);
      dashboardData = data;
      
      if (!data || !data.stats || !data.mentions || !data.timeline) {
        throw new Error('Invalid data structure received');
      }
      
      // Update metrics
      updateMetrics(dashboardData.stats);
      
      // Create charts
      createSentimentChart(dashboardData.stats);
      createTimelineChart(dashboardData.timeline);
      
      // Populate mentions table
      populateMentionsTable(dashboardData.mentions);
      
      // Show the dashboard content
      showDashboard();
    })
    .catch(error => {
      console.error('Error loading dashboard data:', error);
      handleError(error);
    });
});

// Update the metrics cards with data
function updateMetrics(stats) {
  console.log('Updating metrics with stats:', stats);
  
  if (!stats) {
    console.error('No stats provided to updateMetrics');
    return;
  }
  
  document.getElementById('total-mentions').textContent = stats.TOTAL || 0;
  
  const avgScore = (stats.AVG_SCORE || 0).toFixed(2);
  document.getElementById('sentiment-score').textContent = avgScore;
  
  // Update progress bars
  const positiveWidth = Math.max(0, (stats.AVG_SCORE || 0) * 100);
  const negativeWidth = Math.max(0, -(stats.AVG_SCORE || 0) * 100);
  document.getElementById('positive-progress').style.width = positiveWidth + '%';
  document.getElementById('negative-progress').style.width = negativeWidth + '%';
  
  // Calculate percentages
  const total = stats.TOTAL || 1; // Avoid division by zero
  const positivePct = ((stats.POSITIVE || 0) / total * 100).toFixed(1);
  const neutralPct = ((stats.NEUTRAL || 0) / total * 100).toFixed(1);
  const negativePct = ((stats.NEGATIVE || 0) / total * 100).toFixed(1);
  
  document.getElementById('positive-pct').textContent = positivePct + '%';
  document.getElementById('neutral-pct').textContent = neutralPct + '%';
  document.getElementById('negative-pct').textContent = negativePct + '%';
}

// Create the sentiment distribution chart
function createSentimentChart(stats) {
  const data = [
    {
      x: ['Positive', 'Neutral', 'Negative'],
      y: [stats.POSITIVE, stats.NEUTRAL, stats.NEGATIVE],
      type: 'bar',
      marker: {
        color: ['#28a745', '#6c757d', '#dc3545']
      },
      text: [stats.POSITIVE, stats.NEUTRAL, stats.NEGATIVE],
      textposition: 'auto'
    }
  ];
  
  const layout = {
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
    margin: {l: 40, r: 20, t: 20, b: 40},
    height: 300,
    xaxis: {
      title: '',
      fixedrange: true
    },
    yaxis: {
      title: 'Number of Mentions',
      fixedrange: true
    }
  };
  
  const config = {responsive: true, displayModeBar: false};
  
  Plotly.newPlot('sentiment-chart', data, layout, config);
}

// Create the sentiment timeline chart
function createTimelineChart(timelineData) {
  // Prepare data for the chart
  const dates = timelineData.map(item => item.date);
  const scores = timelineData.map(item => item.score);
  const sentiments = timelineData.map(item => item.sentiment);
  
  // Create color mapping for sentiments
  const colors = sentiments.map(sentiment => {
    if (sentiment === 'POSITIVE') return '#28a745';
    if (sentiment === 'NEGATIVE') return '#dc3545';
    return '#6c757d'; // NEUTRAL
  });
  
  // Create scatter plot
  const scatterTrace = {
    x: dates,
    y: scores,
    mode: 'markers',
    type: 'scatter',
    marker: {
      color: colors,
      size: 10
    },
    name: 'Sentiment'
  };
  
  // Add trend line if we have enough data points
  let traces = [scatterTrace];
  if (timelineData.length >= 2) {
    // Simple linear trend line (in a real implementation, this would be more sophisticated)
    const trendTrace = {
      x: dates,
      y: calculateTrendLine(dates, scores),
      mode: 'lines',
      type: 'scatter',
      line: {
        color: 'rgba(100, 100, 100, 0.5)',
        width: 2
      },
      name: 'Trend'
    };
    traces.push(trendTrace);
  }
  
  const layout = {
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
    margin: {l: 40, r: 20, t: 20, b: 40},
    height: 300,
    xaxis: {
      title: 'Date',
      fixedrange: true
    },
    yaxis: {
      title: 'Sentiment Score',
      range: [-1.1, 1.1],
      zeroline: true,
      zerolinecolor: 'rgba(0,0,0,0.2)',
      zerolinewidth: 1,
      fixedrange: true
    },
    showlegend: true,
    legend: {
      orientation: 'h',
      yanchor: 'bottom',
      y: 1.02,
      xanchor: 'right',
      x: 1
    }
  };
  
  const config = {responsive: true, displayModeBar: false};
  
  Plotly.newPlot('timeline-chart', traces, layout, config);
}

// Simple linear regression for trend line
function calculateTrendLine(dates, scores) {
  // Convert dates to numeric values for calculation
  const xValues = dates.map((_, i) => i);
  const yValues = scores;
  
  // Calculate means
  const xMean = xValues.reduce((sum, val) => sum + val, 0) / xValues.length;
  const yMean = yValues.reduce((sum, val) => sum + val, 0) / yValues.length;
  
  // Calculate slope and intercept
  let numerator = 0;
  let denominator = 0;
  
  for (let i = 0; i < xValues.length; i++) {
    numerator += (xValues[i] - xMean) * (yValues[i] - yMean);
    denominator += Math.pow(xValues[i] - xMean, 2);
  }
  
  const slope = numerator / denominator;
  const intercept = yMean - (slope * xMean);
  
  // Generate trend line values
  return xValues.map(x => slope * x + intercept);
}

// Populate the mentions table
function populateMentionsTable(mentions) {
  const tableContainer = document.getElementById('mentions-table');
  
  if (mentions.length === 0) {
    tableContainer.innerHTML = '<p>No mentions available.</p>';
    return;
  }
  
  // Create table
  const table = document.createElement('table');
  table.className = 'table table-striped';
  
  // Create table header
  const thead = document.createElement('thead');
  thead.innerHTML = `
    <tr>
      <th>Date</th>
      <th>Title</th>
      <th>Source</th>
      <th>Sentiment</th>
      <th>Score</th>
      <th>Link</th>
    </tr>
  `;
  table.appendChild(thead);
  
  // Create table body
  const tbody = document.createElement('tbody');
  
  mentions.forEach(mention => {
    const row = document.createElement('tr');
    
    // Add sentiment-based styling
    if (mention.sentiment === 'POSITIVE') {
      row.className = 'table-success';
    } else if (mention.sentiment === 'NEGATIVE') {
      row.className = 'table-danger';
    }
    
    row.innerHTML = `
      <td>${mention.published_at}</td>
      <td>${mention.title}</td>
      <td>${mention.source}</td>
      <td>${mention.sentiment.charAt(0) + mention.sentiment.slice(1).toLowerCase()}</td>
      <td>${mention.sentiment_score.toFixed(2)}</td>
      <td><a href="${mention.url}" target="_blank">View</a></td>
    `;
    
    tbody.appendChild(row);
  });
  
  table.appendChild(tbody);
  tableContainer.innerHTML = '';
  tableContainer.appendChild(table);
}