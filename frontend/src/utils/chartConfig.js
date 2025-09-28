import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Define a color palette
export const colors = {
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  danger: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  }
};

export const getSeverityColor = (severity) => {
  switch (severity?.toUpperCase()) {
    case 'ERROR':
    case 'CRITICAL':
      return colors.danger[500];
    case 'WARNING':
    case 'HIGH':
      return colors.warning[500];
    case 'INFO':
    case 'LOW':
      return colors.success[500];
    default:
      return colors.gray[500];
  }
};

export const getRiskColors = (risks) => {
  if (!risks.length) {
    return {
      background: [colors.gray[200]],
      border: [colors.gray[400]],
    };
  }

  return {
    background: risks.map(() => colors.primary[200]),
    border: risks.map(() => colors.primary[600]),
  };
};

export const createChartData = (risks) => ({
  labels: risks.length ? risks.map((risk) => risk.name) : ['No risks'],
  datasets: [
    {
      label: 'Risk Level',
      data: risks.length ? risks.map((risk) => risk.level) : [0],
      backgroundColor: getRiskColors(risks).background,
      borderColor: getRiskColors(risks).border,
      borderWidth: 2,
      borderRadius: 4,
      borderSkipped: false,
    },
  ],
});

export const createChartOptions = (risks) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { 
      display: false 
    },
    title: {
      display: true,
      text: 'Risk Distribution by Severity Level',
      color: colors.gray[700],
      font: { 
        size: 18,
        weight: '600'
      },
      padding: 20,
    },
    tooltip: {
      backgroundColor: colors.gray[800],
      titleColor: colors.gray[100],
      bodyColor: colors.gray[100],
      borderColor: colors.gray[600],
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: false,
    },
  },
  scales: {
    x: {
      ticks: { 
        color: colors.gray[600],
        font: { size: 12 }
      },
      grid: { 
        color: colors.gray[200],
        drawOnChartArea: false,
      },
    },
    y: {
      ticks: { 
        color: colors.gray[600],
        font: { size: 12 }
      },
      grid: { 
        color: colors.gray[200] 
      },
      beginAtZero: true,
      title: {
        display: true,
        text: 'Risk Score',
        color: colors.gray[700],
        font: { 
          size: 14,
          weight: '500'
        },
      },
      suggestedMax: Math.max(...(risks.map((r) => r.level) || [10]), 10) + 5,
    },
  },
});