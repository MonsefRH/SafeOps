import { 
  DocumentTextIcon, 
  DocumentDuplicateIcon, 
  ClockIcon, 
  CloudArrowDownIcon, 
  CodeBracketSquareIcon, 
  ListBulletIcon 
} from '@heroicons/react/24/outline';

// Import configuration files
import JenkinsfileContent from '../configs/Jenkinsfile';
import GitLabCIContent from '../configs/GitlabCi';
import GitHubActionsContent from '../configs/GithubActions';

// Color palette for policies generator
export const complianceColors = {
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
  secondary: {
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
  },
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
};

// Source type configurations
export const sourceTypeConfig = [
  {
    type: 'selected_repos',
    label: 'Selected repositories',
    icon: <ListBulletIcon className="w-5 h-5" />,
    description: 'Generate policies for your selected repositories'
  },
  {
    type: 'github',
    label: 'GitHub link',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.135 1.838 1.24 1.838 1.24 1.065 1.885 2.876 1.34 3.578 1.025.112-.795.434-1.34.792-1.645-2.776-.315-5.686-1.385-5.686-6.165 0-1.365.487-2.48 1.287-3.355-.13-.315-.558-1.585.123-3.305 0 0 1.05-.335 3.44 1.285A12.01 12.01 0 0112 4.8c1.065.005 2.135.145 3.14.43 2.39-1.62 3.435-1.285 3.435-1.285.685 1.72.255 2.99.125 3.305.805.875 1.285 1.99 1.285 3.355 0 4.795-2.915 5.845-5.695 6.155.445.385.84 1.145.84 2.31 0 1.665-.015 3.015-.015 3.42 0 .32.215.695.825.575C20.565 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
      </svg>
    ),
    description: 'Generate policies from a GitHub repository URL'
  },
  {
    type: 'code',
    label: 'Code',
    icon: <CodeBracketSquareIcon className="h-5 w-5" />,
    description: 'Paste your code directly for policy generation'
  },
  {
    type: 'file',
    label: 'File',
    icon: <CloudArrowDownIcon className="h-5 w-5" />,
    description: 'Upload files for policy generation'
  },
  {
    type: 'jenkinsfile',
    label: 'Jenkinsfile',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.514 0 10 4.486 10 10s-4.486 10-10 10S2 17.514 2 12 6.486 2 12 2zm0 3a1 1 0 00-1 1v4H8a1 1 0 100 2h3v4a1 1 0 102 0v-4h3a1 1 0 100-2h-3V6a1 1 0 00-1-1z" />
      </svg>
    ),
    description: 'View and copy Jenkinsfile configuration'
  },
  {
    type: 'githubactions',
    label: 'GitHub Actions',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.135 1.838 1.24 1.838 1.24 1.065 1.885 2.876 1.34 3.578 1.025.112-.795.434-1.34.792-1.645-2.776-.315-5.686-1.385-5.686-6.165 0-1.365.487-2.48 1.287-3.355-.13-.315-.558-1.585.123-3.305 0 0 1.05-.335 3.44 1.285A12.01 12.01 0 0112 4.8c1.065.005 2.135.145 3.14.43 2.39-1.62 3.435-1.285 3.435-1.285.685 1.72.255 2.99.125 3.305.805.875 1.285 1.99 1.285 3.355 0 4.795-2.915 5.845-5.695 6.155.445.385.84 1.145.84 2.31 0 1.665-.015 3.015-.015 3.42 0 .32.215.695.825.575C20.565 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
      </svg>
    ),
    description: 'View and copy GitHub Actions workflow'
  },
  {
    type: 'gitlabci',
    label: 'GitLab CI/CD',
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.64 14.67l-1.31-4-2.09-6.36a.66.66 0 00-.63-.45.66.66 0 00-.63.45l-2.09 6.36h-4.18L10.62 4.31a.66.66 0 00-.63-.45.66.66 0 00-.63.45l-2.09 6.36H3.07L1.76 14.67a.66.66 0 00.24.81l9.55 6.95a.66.66 0 00.78 0l9.55-6.95a.66.66 0 00.24-.81zm-15.2-2.5l1.31-4 1.31 4H8.44zm7.12 0l1.31-4 1.31 4h-2.62z" />
      </svg>
    ),
    description: 'View and copy GitLab CI/CD configuration'
  },
];

// Code configurations
export const codeConfigurations = {
  jenkinsfile: {
    content: JenkinsfileContent,
    label: 'Jenkinsfile',
    language: 'groovy'
  },
  gitlabci: {
    content: GitLabCIContent,
    label: 'GitLab CI/CD',
    language: 'yaml'
  },
  githubactions: {
    content: GitHubActionsContent,
    label: 'GitHub Actions',
    language: 'yaml'
  },
};

// Check if source type is a code configuration
export const isCodeConfiguration = (sourceType) => {
  return codeConfigurations.hasOwnProperty(sourceType);
};

// Get code configuration
export const getCodeConfiguration = (sourceType) => {
  return codeConfigurations[sourceType] || null;
};

// Animation configurations
export const animationConfig = {
  transition: {
    duration: 300,
    easing: 'ease-in-out'
  },
  fadeIn: 'opacity-0',
  fadeOut: 'opacity-100',
};

// Toast configurations
export const toastConfig = {
  position: 'top-right',
  autoClose: 3000,
  theme: 'light',
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

// Button configurations
export const buttonConfig = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-blue-600 hover:bg-blue-700 text-white',
  neutral: 'bg-gray-600 hover:bg-gray-700 text-white',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
  success: 'bg-green-600 hover:bg-green-700 text-white',
};