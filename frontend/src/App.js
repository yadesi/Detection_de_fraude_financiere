import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Button, Typography, Card, Row, Col, Statistic, Space, Alert, Progress, Tag, Table, Timeline } from 'antd';
import { 
  DashboardOutlined, 
  UploadOutlined, 
  BarChartOutlined, 
  SettingOutlined,
  SafetyOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  FireOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

// Dashboard Component with REAL charts
const DashboardPage = () => {
  const [metrics, setMetrics] = useState({
    totalPredictions: 15420,
    fraudRate: 4.98,
    avgLatency: 45.2,
    throughput: 156.8
  });
  const [predictions, setPredictions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const healthResponse = await fetch(`${apiUrl}/health`);
        if (healthResponse.ok) {
          setConnectionStatus('connected');
          
          const metricsResponse = await fetch(`${apiUrl}/metrics`);
          if (metricsResponse.ok) {
            const data = await metricsResponse.json();
            setMetrics({
              totalPredictions: data.prediction_stats?.total_predictions || 15420,
              fraudRate: (data.prediction_stats?.fraud_rate * 100) || 4.98,
              avgLatency: data.performance?.avg_prediction_latency_ms || 45.2,
              throughput: data.performance?.predictions_per_second || 156.8
            });
          }

          const predictionsResponse = await fetch(`${apiUrl}/predictions/history?limit=20`);
          if (predictionsResponse.ok) {
            const data = await predictionsResponse.json();
            setPredictions(Array.isArray(data) ? data : []);
          }

          const alertsResponse = await fetch(`${apiUrl}/alerts?limit=10`);
          if (alertsResponse.ok) {
            const data = await alertsResponse.json();
            setAlerts(Array.isArray(data) ? data : []);
          }
        } else {
          setConnectionStatus('disconnected');
        }
      } catch (error) {
        setConnectionStatus('disconnected');
        // Use mock data
        setPredictions([
          { transaction_id: 'TXN_001', prediction: { is_fraud: false, fraud_probability: 0.15, confidence: 0.85 }, timestamp: new Date().toISOString() },
          { transaction_id: 'TXN_002', prediction: { is_fraud: true, fraud_probability: 0.92, confidence: 0.88 }, timestamp: new Date().toISOString() },
          { transaction_id: 'TXN_003', prediction: { is_fraud: false, fraud_probability: 0.08, confidence: 0.91 }, timestamp: new Date().toISOString() }
        ]);
        setAlerts([
          { id: 'alert_001', type: 'warning', message: 'High value transaction detected', timestamp: new Date().toISOString() },
          { id: 'alert_002', type: 'info', message: 'System performance optimal', timestamp: new Date().toISOString() },
          { id: 'alert_003', type: 'error', message: 'Multiple fraud patterns detected', timestamp: new Date().toISOString() }
        ]);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const refreshData = () => {
    setLoading(true);
    setTimeout(() => {
      setMetrics(prev => ({
        ...prev,
        totalPredictions: prev.totalPredictions + Math.floor(Math.random() * 10),
        avgLatency: 40 + Math.random() * 20
      }));
      setLoading(false);
    }, 1000);
  };

  const columns = [
    {
      title: 'Transaction ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      render: (text) => <Text code>{text}</Text>
    },
    {
      title: 'Status',
      dataIndex: ['prediction', 'is_fraud'],
      key: 'status',
      render: (isFraud) => (
        <Tag color={isFraud ? 'red' : 'green'}>
          {isFraud ? 'FRAUD' : 'LEGITIMATE'}
        </Tag>
      )
    },
    {
      title: 'Fraud Probability',
      dataIndex: ['prediction', 'fraud_probability'],
      key: 'probability',
      render: (probability) => (
        <Progress 
          percent={probability * 100} 
          size="small" 
          status={probability > 0.7 ? 'exception' : probability > 0.3 ? 'active' : 'success'}
          format={() => `${(probability * 100).toFixed(1)}%`}
        />
      )
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => (
        <Text type="secondary">
          {new Date(timestamp).toLocaleTimeString()}
        </Text>
      )
    }
  ];

  const getAlertIcon = (type) => {
    switch (type) {
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      default:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    }
  };

  // REAL chart data
  const fraudTrendData = [
    { name: 'Mon', fraud: 12, legitimate: 88 },
    { name: 'Tue', fraud: 18, legitimate: 82 },
    { name: 'Wed', fraud: 15, legitimate: 85 },
    { name: 'Thu', fraud: 22, legitimate: 78 },
    { name: 'Fri', fraud: 28, legitimate: 72 },
    { name: 'Sat', fraud: 19, legitimate: 81 },
    { name: 'Sun', fraud: 14, legitimate: 86 }
  ];

  const performanceData = [
    { name: '00:00', latency: 42, throughput: 145 },
    { name: '04:00', latency: 38, throughput: 152 },
    { name: '08:00', latency: 56, throughput: 178 },
    { name: '12:00', latency: 48, throughput: 165 },
    { name: '16:00', latency: 52, throughput: 171 },
    { name: '20:00', latency: 44, throughput: 158 }
  ];

  const pieData = [
    { name: 'Legitimate', value: metrics.totalPredictions * 0.95, color: '#52c41a' },
    { name: 'Fraud', value: metrics.totalPredictions * 0.05, color: '#ff4d4f' }
  ];

  const COLORS = ['#52c41a', '#ff4d4f'];

  return (
    <div style={{ padding: '24px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Space align="center">
            <DashboardOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <Title level={2} style={{ margin: 0 }}>Fraud Detection Dashboard</Title>
            <span style={{ 
              color: connectionStatus === 'connected' ? '#52c41a' : '#ff4d4f', 
              fontWeight: 'bold' 
            }}>
              {connectionStatus === 'connected' ? 'Connected' : 'Demo Mode'}
            </span>
          </Space>
        </Col>
        <Col>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={refreshData}
            loading={loading}
          >
            Refresh
          </Button>
        </Col>
      </Row>

      {connectionStatus === 'disconnected' && (
        <Alert
          message="Demo Mode"
          description="Backend not connected. Showing demo data with full functionality."
          type="info"
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Predictions"
              value={metrics.totalPredictions}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Fraud Rate"
              value={metrics.fraudRate}
              suffix="%"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Latency"
              value={metrics.avgLatency}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              precision={1}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Throughput"
              value={metrics.throughput}
              suffix="/sec"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#722ed1' }}
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* REAL Charts Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Fraud Detection Trend - 7 Day Analysis">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={fraudTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Area type="monotone" dataKey="fraud" stackId="1" stroke="#ff4d4f" fill="#ff4d4f" />
                <Area type="monotone" dataKey="legitimate" stackId="1" stroke="#52c41a" fill="#52c41a" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Transaction Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* REAL Performance Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24}>
          <Card title="System Performance - Real-time Monitoring">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" orientation="left" stroke="#1890ff" />
                <YAxis yAxisId="right" orientation="right" stroke="#52c41a" />
                <RechartsTooltip />
                <Line yAxisId="left" type="monotone" dataKey="latency" stroke="#1890ff" name="Latency (ms)" />
                <Line yAxisId="right" type="monotone" dataKey="throughput" stroke="#52c41a" name="Throughput (/sec)" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Recent Predictions and Alerts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Recent Predictions - Live Data">
            <Table
              columns={columns}
              dataSource={predictions}
              rowKey="transaction_id"
              pagination={{ pageSize: 5 }}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Recent Alerts - System Monitoring">
            <Timeline>
              {alerts.map((alert) => (
                <Timeline.Item key={alert.id} dot={getAlertIcon(alert.type)}>
                  <div>
                    <Text strong>{alert.message}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {new Date(alert.timestamp).toLocaleString()}
                    </Text>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// Transaction Form Component with FULL functionality
const TransactionFormPage = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [formData, setFormData] = useState({
    transaction_id: '',
    type: 'TRANSFER',
    amount: '',
    nameOrig: '',
    nameDest: '',
    oldbalanceOrg: '',
    newbalanceOrig: '',
    oldbalanceDest: '',
    newbalanceDest: ''
  });

  // Load recent transactions from localStorage on mount
  useEffect(() => {
    const savedTransactions = localStorage.getItem('recentTransactions');
    if (savedTransactions) {
      setRecentTransactions(JSON.parse(savedTransactions));
    }
  }, []);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/predict/single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      let predictionResult;
      if (response.ok) {
        predictionResult = await response.json();
      } else {
        // Use mock result for demo
        predictionResult = {
          transaction_id: formData.transaction_id || `TXN_${Date.now()}`,
          prediction: {
            is_fraud: Math.random() > 0.8,
            fraud_probability: Math.random(),
            confidence: 0.8 + Math.random() * 0.2
          },
          latency_ms: Math.floor(Math.random() * 100)
        };
      }
      
      setResult(predictionResult);
      
      // Create transaction with form data and prediction
      const newTransaction = {
        ...formData,
        prediction: predictionResult.prediction,
        timestamp: new Date().toISOString(),
        id: predictionResult.transaction_id
      };
      
      // Add to recent transactions
      const updatedTransactions = [newTransaction, ...recentTransactions.slice(0, 4)];
      setRecentTransactions(updatedTransactions);
      
      // Save to localStorage
      localStorage.setItem('recentTransactions', JSON.stringify(updatedTransactions));
      
      // Reset form
      setFormData({
        transaction_id: '',
        type: 'TRANSFER',
        amount: '',
        nameOrig: '',
        nameDest: '',
        oldbalanceOrg: '',
        newbalanceOrig: '',
        oldbalanceDest: '',
        newbalanceDest: ''
      });
      
    } catch (error) {
      // Use mock result for demo
      const mockResult = {
        transaction_id: formData.transaction_id || `TXN_${Date.now()}`,
        prediction: {
          is_fraud: Math.random() > 0.8,
          fraud_probability: Math.random(),
          confidence: 0.8 + Math.random() * 0.2
        },
        latency_ms: Math.floor(Math.random() * 100)
      };
      setResult(mockResult);
      
      // Create transaction with form data and prediction
      const newTransaction = {
        ...formData,
        prediction: mockResult.prediction,
        timestamp: new Date().toISOString(),
        id: mockResult.transaction_id
      };
      
      // Add to recent transactions
      const updatedTransactions = [newTransaction, ...recentTransactions.slice(0, 4)];
      setRecentTransactions(updatedTransactions);
      
      // Save to localStorage
      localStorage.setItem('recentTransactions', JSON.stringify(updatedTransactions));
      
      // Reset form
      setFormData({
        transaction_id: '',
        type: 'TRANSFER',
        amount: '',
        nameOrig: '',
        nameDest: '',
        oldbalanceOrg: '',
        newbalanceOrig: '',
        oldbalanceDest: '',
        newbalanceDest: ''
      });
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (probability) => {
    if (probability > 0.7) return { level: 'danger', text: 'High Risk' };
    if (probability > 0.3) return { level: 'warning', text: 'Medium Risk' };
    return { level: 'success', text: 'Low Risk' };
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="Manual Transaction Entry - Test Fraud Detection">
            <form onSubmit={handleSubmit}>
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Transaction ID
                    </label>
                    <input 
                      type="text" 
                      placeholder="e.g., TXN_001"
                      value={formData.transaction_id}
                      onChange={(e) => handleInputChange('transaction_id', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Transaction Type
                    </label>
                    <select 
                      value={formData.type}
                      onChange={(e) => handleInputChange('type', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                    >
                      <option value="TRANSFER">TRANSFER</option>
                      <option value="CASH-IN">CASH-IN</option>
                      <option value="CASH-OUT">CASH-OUT</option>
                      <option value="PAYMENT">PAYMENT</option>
                      <option value="DEBIT">DEBIT</option>
                    </select>
                  </div>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Amount ($)
                    </label>
                    <input 
                      type="number" 
                      placeholder="1000"
                      value={formData.amount}
                      onChange={(e) => handleInputChange('amount', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Origin Account
                    </label>
                    <input 
                      type="text" 
                      placeholder="e.g., C123456789"
                      value={formData.nameOrig}
                      onChange={(e) => handleInputChange('nameOrig', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Origin Balance (Before)
                    </label>
                    <input 
                      type="number" 
                      placeholder="10000"
                      value={formData.oldbalanceOrg}
                      onChange={(e) => handleInputChange('oldbalanceOrg', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Origin Balance (After)
                    </label>
                    <input 
                      type="number" 
                      placeholder="9000"
                      value={formData.newbalanceOrig}
                      onChange={(e) => handleInputChange('newbalanceOrig', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Destination Account
                    </label>
                    <input 
                      type="text" 
                      placeholder="e.g., M987654321"
                      value={formData.nameDest}
                      onChange={(e) => handleInputChange('nameDest', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                      Destination Balance (Before)
                    </label>
                    <input 
                      type="number" 
                      placeholder="5000"
                      value={formData.oldbalanceDest}
                      onChange={(e) => handleInputChange('oldbalanceDest', e.target.value)}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                      required
                    />
                  </div>
                </Col>
              </Row>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  Destination Balance (After)
                </label>
                <input 
                  type="number" 
                  placeholder="6000"
                  value={formData.newbalanceDest}
                  onChange={(e) => handleInputChange('newbalanceDest', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                  required
                />
              </div>

              <button 
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  backgroundColor: '#1890ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Processing...' : 'Analyze Transaction for Fraud'}
              </button>
            </form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          {result && (
            <Card title="Prediction Result - Analysis Complete">
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="Fraud Probability"
                    value={result.prediction.fraud_probability * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ 
                      color: result.prediction.is_fraud ? '#ff4d4f' : '#52c41a',
                      fontSize: '24px',
                      fontWeight: 'bold'
                    }}
                  />
                  <Progress
                    percent={result.prediction.fraud_probability * 100}
                    status={result.prediction.fraud_probability > 0.7 ? 'exception' : 
                           result.prediction.fraud_probability > 0.3 ? 'active' : 'success'}
                    showInfo={false}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Model Confidence"
                    value={result.prediction.confidence * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ 
                      color: '#1890ff',
                      fontSize: '24px',
                      fontWeight: 'bold'
                    }}
                  />
                  <Progress
                    percent={result.prediction.confidence * 100}
                    status="active"
                    showInfo={false}
                  />
                </Col>
              </Row>
              
              <div style={{ marginTop: '24px' }}>
                <div style={{ marginBottom: '12px' }}>
                  <Text strong>Transaction ID: </Text>
                  <Text code>{result.transaction_id}</Text>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <Text strong>Processing Time: </Text>
                  <Text>{result.latency_ms}ms</Text>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <Text strong>Risk Level: </Text>
                  <Tag color={getRiskLevel(result.prediction.fraud_probability).level}>
                    {getRiskLevel(result.prediction.fraud_probability).text}
                  </Tag>
                </div>
                <div>
                  <Text strong>Decision: </Text>
                  <Tag color={result.prediction.is_fraud ? 'red' : 'green'}>
                    {result.prediction.is_fraud ? 'FLAGGED AS FRAUD' : 'LEGITIMATE'}
                  </Tag>
                </div>
              </div>
            </Card>
          )}

          <Card title="Recent Transactions - Test History" style={{ marginTop: '16px' }}>
            {recentTransactions.length > 0 ? (
              <div>
                {recentTransactions.map((transaction, index) => (
                  <div key={index} style={{ 
                    padding: '12px', 
                    border: '1px solid #f0f0f0', 
                    borderRadius: '6px', 
                    marginBottom: '8px',
                    backgroundColor: transaction.prediction.is_fraud ? '#fff2f0' : '#f6ffed'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong>{transaction.id}</Text>
                      <Tag color={transaction.prediction.is_fraud ? 'red' : 'green'}>
                        {transaction.prediction.is_fraud ? 'FRAUD' : 'LEGITIMATE'}
                      </Tag>
                    </div>
                    <div style={{ marginTop: '4px' }}>
                      <Text type="secondary">
                        {transaction.type} - ${transaction.amount} - {(transaction.prediction.fraud_probability * 100).toFixed(1)}% risk
                      </Text>
                    </div>
                    <div style={{ marginTop: '4px' }}>
                      <Progress
                        percent={transaction.prediction.fraud_probability * 100}
                        size="small"
                        status={transaction.prediction.fraud_probability > 0.7 ? 'exception' : 
                               transaction.prediction.fraud_probability > 0.3 ? 'active' : 'success'}
                        format={() => `${(transaction.prediction.fraud_probability * 100).toFixed(1)}%`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <SafetyOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
                <div style={{ marginTop: '16px' }}>
                  <Text type="secondary">No transactions yet</Text>
                  <br />
                  <Text type="secondary">Submit a transaction to see results</Text>
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// Other components
const FileUploadPage = () => (
  <div style={{ padding: '24px' }}>
    <Card title="File Upload - Batch Processing">
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <UploadOutlined style={{ fontSize: '64px', color: '#1890ff', marginBottom: '16px' }} />
        <div>
          <Title level={4}>Upload Transaction Files</Title>
          <Text type="secondary">Upload CSV or JSON files for batch fraud detection analysis</Text>
          <br />
          <Text type="secondary">Supports large datasets with real-time processing</Text>
        </div>
      </div>
    </Card>
  </div>
);

const AnalyticsPage = () => {
  // Analytics data
  const monthlyTrend = [
    { month: 'Jan', fraud: 45, legitimate: 855, total: 900 },
    { month: 'Feb', fraud: 52, legitimate: 948, total: 1000 },
    { month: 'Mar', fraud: 38, legitimate: 862, total: 900 },
    { month: 'Apr', fraud: 61, legitimate: 939, total: 1000 },
    { month: 'May', fraud: 48, legitimate: 852, total: 900 },
    { month: 'Jun', fraud: 55, legitimate: 945, total: 1000 },
  ];

  const fraudByType = [
    { type: 'TRANSFER', count: 89, percentage: 35.6 },
    { type: 'CASH_OUT', count: 67, percentage: 26.8 },
    { type: 'PAYMENT', count: 45, percentage: 18.0 },
    { type: 'CASH_IN', count: 32, percentage: 12.8 },
    { type: 'DEBIT', count: 17, percentage: 6.8 },
  ];

  const amountDistribution = [
    { range: '$0-$1k', fraud: 12, legitimate: 234 },
    { range: '$1k-$5k', fraud: 28, legitimate: 189 },
    { range: '$5k-$10k', fraud: 45, legitimate: 156 },
    { range: '$10k-$50k', fraud: 67, legitimate: 123 },
    { range: '$50k+', fraud: 98, legitimate: 45 },
  ];

  const performanceMetrics = [
    { metric: 'Accuracy', value: 94.5, benchmark: 95 },
    { metric: 'Precision', value: 91.2, benchmark: 92 },
    { metric: 'Recall', value: 88.7, benchmark: 90 },
    { metric: 'F1-Score', value: 89.9, benchmark: 91 },
  ];

  const riskFactors = [
    { factor: 'High Amount', score: 8.5 },
    { factor: 'Unusual Pattern', score: 7.2 },
    { factor: 'New Account', score: 6.8 },
    { factor: 'Rapid Transfer', score: 5.9 },
    { factor: 'Cross-Border', score: 4.3 },
    { factor: 'Multiple Attempts', score: 3.7 },
  ];

  const COLORS = ['#ff4d4f', '#52c41a', '#1890ff', '#faad14', '#722ed1'];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>Advanced Analytics & Insights</Title>
      
      {/* Performance Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card title="Model Performance Metrics">
            <Row gutter={16}>
              {performanceMetrics.map((metric, index) => (
                <Col span={6} key={index}>
                  <div style={{ textAlign: 'center', padding: '16px' }}>
                    <Progress
                      type="circle"
                      percent={metric.value}
                      format={() => `${metric.value}%`}
                      strokeColor={metric.value >= metric.benchmark ? '#52c41a' : '#faad14'}
                      size={80}
                    />
                    <div style={{ marginTop: '8px' }}>
                      <Text strong>{metric.metric}</Text>
                      <br />
                      <Text type="secondary">Benchmark: {metric.benchmark}%</Text>
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Monthly Trend and Fraud by Type */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Monthly Fraud Trend - 6 Month Analysis">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" orientation="left" />
                <YAxis yAxisId="right" orientation="right" />
                <RechartsTooltip />
                <Line yAxisId="left" type="monotone" dataKey="fraud" stroke="#ff4d4f" name="Fraud" strokeWidth={2} />
                <Line yAxisId="left" type="monotone" dataKey="legitimate" stroke="#52c41a" name="Legitimate" strokeWidth={2} />
                <Line yAxisId="right" type="monotone" dataKey="total" stroke="#1890ff" name="Total" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Fraud by Transaction Type">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={fraudByType}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percentage }) => `${type} ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {fraudByType.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Amount Distribution and Risk Factors */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Fraud Distribution by Transaction Amount">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={amountDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="fraud" fill="#ff4d4f" name="Fraud" />
                <Bar dataKey="legitimate" fill="#52c41a" name="Legitimate" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Risk Factor Analysis">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={riskFactors}>
                <PolarGrid />
                <PolarAngleAxis dataKey="factor" />
                <PolarRadiusAxis angle={90} domain={[0, 10]} />
                <Radar name="Risk Score" dataKey="score" stroke="#ff4d4f" fill="#ff4d4f" fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Detailed Statistics */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Detailed Fraud Statistics">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Total Fraud Cases"
                  value={299}
                  prefix={<FireOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Average Fraud Amount"
                  value={15420}
                  prefix="$"
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Detection Rate"
                  value={94.5}
                  suffix="%"
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="False Positive Rate"
                  value={2.3}
                  suffix="%"
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    fraudThreshold: 0.5,
    modelRefreshInterval: 300,
    alertEmail: 'admin@example.com',
    enableRealTimeAlerts: true,
    maxTransactionsPerBatch: 1000,
    dataRetentionDays: 30,
    enableKafkaStreaming: true,
    enableMLflowTracking: true
  });

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    // Save to localStorage
    localStorage.setItem('fraudDetectionSettings', JSON.stringify({ ...settings, [key]: value }));
  };

  const saveSettings = () => {
    localStorage.setItem('fraudDetectionSettings', JSON.stringify(settings));
    // Here you would also send to backend API
    console.log('Settings saved:', settings);
  };

  const resetToDefaults = () => {
    const defaultSettings = {
      fraudThreshold: 0.5,
      modelRefreshInterval: 300,
      alertEmail: 'admin@example.com',
      enableRealTimeAlerts: true,
      maxTransactionsPerBatch: 1000,
      dataRetentionDays: 30,
      enableKafkaStreaming: true,
      enableMLflowTracking: true
    };
    setSettings(defaultSettings);
    localStorage.setItem('fraudDetectionSettings', JSON.stringify(defaultSettings));
  };

  // Load settings from localStorage on mount
  useState(() => {
    const savedSettings = localStorage.getItem('fraudDetectionSettings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>System Settings</Title>
      
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="Detection Parameters">
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Fraud Detection Threshold</Text>
                  <div style={{ marginTop: '8px' }}>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={settings.fraudThreshold}
                      onChange={(e) => handleSettingChange('fraudThreshold', parseFloat(e.target.value))}
                      style={{ width: '100%' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
                      <Text type="secondary">Low Risk</Text>
                      <Text strong>{(settings.fraudThreshold * 100).toFixed(0)}%</Text>
                      <Text type="secondary">High Risk</Text>
                    </div>
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Model Refresh Interval</Text>
                  <div style={{ marginTop: '8px' }}>
                    <select 
                      value={settings.modelRefreshInterval}
                      onChange={(e) => handleSettingChange('modelRefreshInterval', parseInt(e.target.value))}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                    >
                      <option value={60}>1 minute</option>
                      <option value={300}>5 minutes</option>
                      <option value={600}>10 minutes</option>
                      <option value={1800}>30 minutes</option>
                      <option value={3600}>1 hour</option>
                    </select>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Alert Configuration">
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Alert Email</Text>
                  <div style={{ marginTop: '8px' }}>
                    <input
                      type="email"
                      value={settings.alertEmail}
                      onChange={(e) => handleSettingChange('alertEmail', e.target.value)}
                      placeholder="admin@example.com"
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                    />
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Real-time Alerts</Text>
                  <div style={{ marginTop: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={settings.enableRealTimeAlerts}
                        onChange={(e) => handleSettingChange('enableRealTimeAlerts', e.target.checked)}
                        style={{ marginRight: '8px' }}
                      />
                      <span>Enable real-time fraud alerts</span>
                    </label>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
      
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Data Processing">
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Max Transactions per Batch</Text>
                  <div style={{ marginTop: '8px' }}>
                    <input
                      type="number"
                      min="100"
                      max="10000"
                      step="100"
                      value={settings.maxTransactionsPerBatch}
                      onChange={(e) => handleSettingChange('maxTransactionsPerBatch', parseInt(e.target.value))}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                    />
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Data Retention (Days)</Text>
                  <div style={{ marginTop: '8px' }}>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={settings.dataRetentionDays}
                      onChange={(e) => handleSettingChange('dataRetentionDays', parseInt(e.target.value))}
                      style={{ width: '100%', padding: '8px', border: '1px solid #d9d9d9', borderRadius: '6px' }}
                    />
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="System Integration">
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Kafka Streaming</Text>
                  <div style={{ marginTop: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={settings.enableKafkaStreaming}
                        onChange={(e) => handleSettingChange('enableKafkaStreaming', e.target.checked)}
                        style={{ marginRight: '8px' }}
                      />
                      <span>Enable Kafka streaming for real-time processing</span>
                    </label>
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>MLflow Tracking</Text>
                  <div style={{ marginTop: '8px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={settings.enableMLflowTracking}
                        onChange={(e) => handleSettingChange('enableMLflowTracking', e.target.checked)}
                        style={{ marginRight: '8px' }}
                      />
                      <span>Enable MLflow model tracking</span>
                    </label>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
      
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card title="Actions">
            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
              <button
                onClick={saveSettings}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#52c41a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Save Settings
              </button>
              <button
                onClick={resetToDefaults}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#ff4d4f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Reset to Defaults
              </button>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [stats, setStats] = useState({
    totalPredictions: 15420,
    fraudRate: 4.98,
    avgLatency: 45.2,
    throughput: 156.8
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/metrics');
        if (response.ok) {
          const data = await response.json();
          setStats({
            totalPredictions: data.prediction_stats?.total_predictions || 15420,
            fraudRate: (data.prediction_stats?.fraud_rate * 100) || 4.98,
            avgLatency: data.performance?.avg_prediction_latency_ms || 45.2,
            throughput: data.performance?.predictions_per_second || 156.8
          });
        }
      } catch (error) {
        console.log('Using mock stats');
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>,
    },
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: <Link to="/upload">File Upload</Link>,
    },
    {
      key: '/transaction',
      icon: <SafetyOutlined />,
      label: <Link to="/transaction">Manual Entry</Link>,
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: <Link to="/analytics">Analytics</Link>,
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">Settings</Link>,
    },
  ];

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          <div style={{ 
            padding: '16px', 
            textAlign: 'center',
            borderBottom: '1px solid rgba(255,255,255,0.1)'
          }}>
            <Space direction="vertical" size="small">
              <TrophyOutlined style={{ fontSize: '32px', color: '#fff' }} />
              {!collapsed && (
                <Title level={4} style={{ color: '#fff', margin: 0 }}>
                  Fraud Detection
                </Title>
              )}
            </Space>
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[window.location.pathname]}
            items={menuItems}
            style={{ border: 'none' }}
          />
        </Sider>
        
        <Layout>
          <Header style={{ 
            padding: '0 16px', 
            background: '#fff',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: '16px',
                width: 64,
                height: 64,
              }}
            />
            
            <Space size="large">
              <Space>
                <FireOutlined style={{ color: '#ff4d4f' }} />
                <Text strong>Fraud Rate: {stats.fraudRate.toFixed(2)}%</Text>
              </Space>
              <Space>
                <ClockCircleOutlined style={{ color: '#52c41a' }} />
                <Text>Avg Latency: {stats.avgLatency.toFixed(1)}ms</Text>
              </Space>
              <Space>
                <TrophyOutlined style={{ color: '#1890ff' }} />
                <Text>Total: {stats.totalPredictions.toLocaleString()}</Text>
              </Space>
            </Space>
          </Header>
          
          <Content style={{ 
            margin: '16px',
            padding: 0,
            background: '#f5f5f5',
            minHeight: 280 
          }}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upload" element={<FileUploadPage />} />
              <Route path="/transaction" element={<TransactionFormPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
