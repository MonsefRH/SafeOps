import React from 'react';
import { ChartBarIcon, ArrowPathIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { Bar } from 'react-chartjs-2';
import { useRisks } from '../../hooks/UseRisk';
import { createChartData, createChartOptions, getSeverityColor } from '../../utils/chartConfig';
import './RiskDashboard.css';

const RiskDashboardPage = () => {
  const { risks, details, loading, error, isRefreshing, refreshRisks } = useRisks();

  // Loading Spinner Component
  const LoadingSpinner = ({ message = 'Loading...' }) => (
    <div className="loading-spinner">
      <ArrowPathIcon className="loading-spinner__icon" />
      <span className="loading-spinner__text">{message}</span>
    </div>
  );

  // Error Message Component
  const ErrorMessage = ({ message, onRetry = null }) => (
    <div className="error-message">
      <div className="error-message__content">
        <ExclamationCircleIcon className="error-message__icon" />
        <div className="error-message__text">
          <h4 className="error-message__title">Something went wrong</h4>
          <p className="error-message__description">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button className="error-message__retry" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );

  // Risk Chart Section
  const RiskChart = ({ risks }) => {
    const chartData = createChartData(risks);
    const chartOptions = createChartOptions(risks);

    return (
      <div className="risk-chart">
        <label htmlFor="risk-chart" className="risk-chart__label">
          Risk Graphical Representation:
        </label>
        <div className="risk-chart__container">
          <Bar id="risk-chart" data={chartData} options={chartOptions} />
        </div>
      </div>
    );
  };

  // Vulnerability Table Section
  const VulnerabilityTable = ({ details }) => {
    if (details.length === 0) {
      return (
        <div className="vulnerability-table">
          <h3 className="vulnerability-table__title">Vulnerability Details</h3>
          <div className="vulnerability-table__empty">
            <p>No vulnerabilities found</p>
          </div>
        </div>
      );
    }

    return (
      <div className="vulnerability-table">
        <h3 className="vulnerability-table__title">
          Vulnerability Details ({details.length})
        </h3>
        
        {/* Desktop Table */}
        <div className="vulnerability-table__desktop">
          <div className="vulnerability-table__scroll">
            <table className="vulnerability-table__table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Problem</th>
                  <th>Suggestion</th>
                </tr>
              </thead>
              <tbody>
                {details.map((detail, index) => (
                  <tr key={index}>
                    <td>
                      <span 
                        className="vulnerability-table__severity"
                        style={{ color: getSeverityColor(detail.severity) }}
                      >
                        {detail.severity}
                      </span>
                    </td>
                    <td className="vulnerability-table__message">
                      {detail.message}
                    </td>
                    <td className="vulnerability-table__suggestion">
                      {detail.suggestion}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Mobile Cards */}
        <div className="vulnerability-table__mobile">
          <div className="vulnerability-table__cards">
            {details.map((detail, index) => (
              <div key={index} className="vulnerability-card">
                <div className="vulnerability-card__header">
                  <span 
                    className="vulnerability-card__severity"
                    style={{ 
                      color: getSeverityColor(detail.severity),
                      borderColor: getSeverityColor(detail.severity)
                    }}
                  >
                    {detail.severity}
                  </span>
                </div>
                <div className="vulnerability-card__content">
                  <div className="vulnerability-card__field">
                    <span className="vulnerability-card__label">Problem:</span>
                    <p className="vulnerability-card__text">{detail.message}</p>
                  </div>
                  <div className="vulnerability-card__field">
                    <span className="vulnerability-card__label">Suggestion:</span>
                    <p className="vulnerability-card__text">{detail.suggestion}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) {
      return <LoadingSpinner message="Loading risks data..." />;
    }

    if (error) {
      return <ErrorMessage message={error} onRetry={refreshRisks} />;
    }

    return (
      <>
        <RiskChart risks={risks} />
        <VulnerabilityTable details={details} />
      </>
    );
  };

  return (
    <div className="risk-dashboard-page">
      <div className="risk-dashboard-page__container">
        <header className="risk-dashboard-page__header">
          <h1 className="risk-dashboard-page__title">
            <ChartBarIcon className="risk-dashboard-page__icon" />
            Risk Management Dashboard
          </h1>
          <button
            className={`risk-dashboard-page__refresh ${
              loading || isRefreshing ? 'risk-dashboard-page__refresh--loading' : ''
            }`}
            onClick={refreshRisks}
            disabled={loading || isRefreshing}
          >
            <ArrowPathIcon 
              className={`risk-dashboard-page__refresh-icon ${
                isRefreshing ? 'risk-dashboard-page__refresh-icon--spinning' : ''
              }`} 
            />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </header>

        <main className="risk-dashboard-page__content">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default RiskDashboardPage;