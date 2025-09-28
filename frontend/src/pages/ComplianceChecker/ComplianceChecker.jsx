import React from 'react';
import { CheckCircleIcon, DocumentDuplicateIcon, ClockIcon } from '@heroicons/react/24/outline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import components (keeping these as they are complex and separate)
import GitHubComplianceChecker from '../../components/ComplianceChecker/GitHubComplianceChecker';
import SelectedReposComplianceChecker from '../../components/ComplianceChecker/SelectedReposComplianceChecker';
import CodeComplianceChecker from '../../components/ComplianceChecker/CodeComplianceChecker';
import FileComplianceChecker from '../../components/ComplianceChecker/FileComplianceChecker';
import ResultDisplay from '../../components/ComplianceChecker/ResultDisplay';
import HistoryModal from '../../components/ComplianceChecker/HistoryModal';

// Import hooks and utilities
import { useCompliance } from '../../hooks/useCompliance';
import { 
  sourceTypeConfig, 
  getCodeConfiguration, 
  isCodeConfiguration,
  toastConfig 
} from '../../utils/complianceConfig';

import './ComplianceChecker.css';

const ComplianceCheckerPage = () => {
  const {
    sourceType,
    result,
    isLoading,
    isHistoryOpen,
    selectedFiles,
    userId,
    setResult,
    setIsLoading,
    resetChecker,
    clearResult,
    openHistory,
    closeHistory,
    handleCopy,
    selectSourceType,
  } = useCompliance();

  // Source Type Selection Component
  const SourceTypeSelection = () => (
    <div className="source-type-selection">
      <h2 className="source-type-selection__title">
        Select a compliance check type:
      </h2>
      <div className="source-type-selection__grid">
        {sourceTypeConfig.map(({ type, label, icon, description }) => (
          <button
            key={type}
            onClick={() => selectSourceType(type)}
            className="source-type-card"
            title={description}
          >
            <div className="source-type-card__icon">
              {icon}
            </div>
            <span className="source-type-card__label">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );

  // Code Display Component
  const CodeDisplay = ({ sourceType }) => {
    const codeConfig = getCodeConfiguration(sourceType);
    
    if (!codeConfig) return null;

    return (
      <div className="code-display">
        <div className="code-display__header">
          <h2 className="code-display__title">{codeConfig.label}</h2>
          <button
            onClick={() => handleCopy(codeConfig.content)}
            className="code-display__copy-btn"
            title="Copy to clipboard"
          >
            <DocumentDuplicateIcon className="code-display__copy-icon" />
            Copy
          </button>
        </div>
        <pre className="code-display__content">
          <code className={`language-${codeConfig.language}`}>
            {codeConfig.content}
          </code>
        </pre>
      </div>
    );
  };

  // Compliance Checker Component
  const ComplianceCheckerComponent = ({ sourceType }) => {
    const checkerProps = {
      setResult,
      isLoading,
      setIsLoading,
      userId
    };

    switch (sourceType) {
      case 'selected_repos':
        return <SelectedReposComplianceChecker {...checkerProps} />;
      case 'github':
        return <GitHubComplianceChecker {...checkerProps} />;
      case 'code':
        return <CodeComplianceChecker {...checkerProps} preSelectedFiles={selectedFiles} />;
      case 'file':
        return <FileComplianceChecker {...checkerProps} />;
      default:
        return null;
    }
  };

  // Results Section Component
  const ResultsSection = () => (
    <div className="results-section">
      <div className="results-section__display">
        <ResultDisplay result={result} userId={userId} />
      </div>
    </div>
  );

  // Action Buttons Component
  const ActionButtons = () => (
    <div className="action-buttons">
      <button
        onClick={resetChecker}
        className="action-buttons__back"
      >
        Back to Selection
      </button>
      {result && (
        <button
          onClick={clearResult}
          className="action-buttons__clear"
        >
          Clear Results
        </button>
      )}
    </div>
  );

  // Main render logic
  const renderContent = () => {
    if (!sourceType) {
      return <SourceTypeSelection />;
    }

    return (
      <div className="compliance-content">
        {/* Render appropriate checker component */}
        {!isCodeConfiguration(sourceType) && (
          <ComplianceCheckerComponent sourceType={sourceType} />
        )}
        
        {/* Render code display for configuration types */}
        {isCodeConfiguration(sourceType) && (
          <CodeDisplay sourceType={sourceType} />
        )}
        
        {/* Results section */}
        <ResultsSection />
        
        {/* Action buttons */}
        <ActionButtons />
      </div>
    );
  };

  return (
    <div className="compliance-checker-page">
      <div className="compliance-checker-page__container checker-content">
        {/* Page Header */}
        <header className="compliance-checker-page__header">
          <h1 className="compliance-checker-page__title">
            <CheckCircleIcon className="compliance-checker-page__title-icon" />
            Compliance Checker
          </h1>
          <button
            onClick={openHistory}
            className="compliance-checker-page__history-btn"
          >
            <ClockIcon className="compliance-checker-page__history-icon" />
            History
          </button>
        </header>

        {/* Main Content */}
        <main className="compliance-checker-page__content">
          {renderContent()}
        </main>

        {/* Toast Notifications */}
        <ToastContainer {...toastConfig} />
        
        {/* History Modal */}
        <HistoryModal
          isOpen={isHistoryOpen}
          onClose={closeHistory}
          userId={userId}
          scanType="compliance"
        />
      </div>
    </div>
  );
};

export default ComplianceCheckerPage;