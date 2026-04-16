import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Table, 
  Tag, 
  Progress, 
  Alert,
  Space,
  Typography,
  Statistic,
  Button,
  Tooltip,
  Spin,
  Badge,
  Divider,
  Timeline,
  Avatar,
  List
} from 'antd';
import { 
  ReloadOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DashboardOutlined,
  SafetyOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  FireOutlined,
  ShieldOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

const { Title, Text, Paragraph } = Typography;

const Dashboard = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Test backend connection first
      const healthResponse = await fetch('http://localhost:8000/health');
      if (!healthResponse.ok) {
        throw new Error('Backend not responding');
      }
      setConnectionStatus('connected');

      // Fetch recent predictions
      try {
        const predictionsResponse = await fetch('http://localhost:8000/predictions/history?limit=10');
        if (predictionsResponse.ok) {
          const predictionsData = await predictionsResponse.json();
          setPredictions(Array.isArray(predictionsData) ? predictionsData : []);
        }
      } catch (err) {
        console.log('Predictions endpoint not available, using mock data');
        setPredictions(generateMockPredictions());
      }

      // Fetch metrics
      try {
        const metricsResponse = await fetch('http://localhost:8000/metrics');
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          setMetrics(metricsData || {});
        }
      } catch (err) {
        console.log('Metrics endpoint not available, using mock data');
        setMetrics(generateMockMetrics());
      }

      // Generate mock alerts for demonstration
      setAlerts(generateMockAlerts());
      
    } catch (err) {
      setError(err.message);
      setConnectionStatus('disconnected');
      // Use mock data when backend is not available
      setPredictions(generateMockPredictions());
      setMetrics(generateMockMetrics());
      setAlerts(generateMockAlerts());
    } finally {
      setLoading(false);
    }
  };

  // Mock data generators for demo purposes
  const generateMockPredictions = () => {
    return [
      { transaction_id: 'TXN_001', prediction: { is_fraud: false, fraud_probability: 0.15, confidence: 0.85 }, timestamp: new Date().toISOString() },
      { transaction_id: 'TXN_002', prediction: { is_fraud: true, fraud_probability: 0.92, confidence: 0.88 }, timestamp: new Date().toISOString() },
      { transaction_id: 'TXN_003', prediction: { is_fraud: false, fraud_probability: 0.08, confidence: 0.91 }, timestamp: new Date().toISOString() },
      { transaction_id: 'TXN_004', prediction: { is_fraud: false, fraud_probability: 0.22, confidence: 0.79 }, timestamp: new Date().toISOString() },
      { transaction_id: 'TXN_005', prediction: { is_fraud: true, fraud_probability: 0.87, confidence: 0.92 }, timestamp: new Date().toISOString() }
    ];
  };

  const generateMockMetrics = () => {
    return {
      prediction_stats: {
        total_predictions: 15420,
        fraud_predictions: 768,
        legitimate_predictions: 14652,
        fraud_rate: 0.0498
      },
      performance: {
        avg_prediction_latency_ms: 45.2,
        error_rate: 0.002,
        predictions_per_second: 156.8
      },
      system: {
        cpu_percent: 42.3,
        memory_percent: 67.8,
        memory_available_gb: 8.2,
        disk_percent: 34.1
      }
    };
  };

  const generateMockAlerts = () => {
    return [
      { id: 'alert_001', type: 'warning', message: 'High value transaction detected', timestamp: new Date().toISOString() },
      { id: 'alert_002', type: 'info', message: 'System performance optimal', timestamp: new Date().toISOString() },
      { id: 'alert_003', type: 'error', message: 'Multiple fraud patterns detected', timestamp: new Date().toISOString() }
    ];
  };

      const getConnectionBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Badge status="success" text="Connected" />;
      case 'disconnected':
        return <Badge status="error" text="Disconnected" />;
      default:
        return <Badge status="processing" text="Connecting..." />;
    }
  };

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
      title: 'Confidence',
      dataIndex: ['prediction', 'confidence'],
      key: 'confidence',
      render: (confidence) => (
        <Progress 
          percent={confidence * 100} 
          size="small" 
          format={() => `${(confidence * 100).toFixed(1)}%`}
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

  // Chart data preparation
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
    { name: 'Legitimate', value: metrics.prediction_stats?.legitimate_predictions || 14652, color: '#52c41a' },
    { name: 'Fraud', value: metrics.prediction_stats?.fraud_predictions || 768, color: '#ff4d4f' }
  ];

  const COLORS = ['#52c41a', '#ff4d4f'];

  if (loading && predictions.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Loading dashboard...</Text>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <Space align="center">
            <DashboardOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <Title level={2} style={{ margin: 0 }}>Fraud Detection Dashboard</Title>
            {getConnectionBadge()}
          </Space>
        </Col>
        <Col>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchDashboardData}
            loading={loading}
          >
            Refresh
          </Button>
        </Col>
      </Row>

      {error && (
        <Alert
          message="Connection Error"
          description={`Unable to connect to backend: ${error}. Showing demo data.`}
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Predictions"
              value={metrics.prediction_stats?.total_predictions || 15420}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Fraud Rate"
              value={((metrics.prediction_stats?.fraud_rate || 0.0498) * 100).toFixed(2)}
              suffix="%"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Latency"
              value={metrics.performance?.avg_prediction_latency_ms || 45.2}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Throughput"
              value={metrics.performance?.predictions_per_second || 156.8}
              suffix="/sec"
              prefix={<TrendingUpOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Fraud Detection Trend" extra={<Badge count="7 Days" />}>
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

      {/* Performance Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24}>
          <Card title="System Performance" extra={<ShieldOutlined />}>
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
          <Card 
            title="Recent Predictions" 
            extra={<Badge count={predictions.length} />}
          >
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
          <Card 
            title="Recent Alerts" 
            extra={<Badge count={alerts.length} />}
          >
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

      )
    },
    {
      title: 'Confidence',
      dataIndex: ['prediction', 'confidence'],
      key: 'confidence',
      render: (confidence) => `${(confidence * 100).toFixed(1)}%`
    },
    {
      title: 'Time',
      dataIndex: ['prediction', 'prediction_timestamp'],
      key: 'prediction_timestamp',
      render: (timestamp) => new Date(timestamp).toLocaleTimeString()
    }
  ];

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <WarningOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    }
  };

  const getAlertColor = (severity) => {
    switch (severity) {
      case 'critical':
        return '#ff4d4f';
      case 'warning':
        return '#faad14';
      default:
        return '#52c41a';
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Real-time Dashboard</Title>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={fetchDashboardData}
          loading={loading}
        >
          Refresh
        </Button>
      </div>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <Title level={4}>Recent Alerts</Title>
          <Row gutter={[16, 16]}>
            {alerts.map((alert, index) => (
              <Col span={8} key={index}>
                <Alert
                  message={alert.type?.replace('_', ' ').toUpperCase()}
                  description={alert.message}
                  type={alert.severity === 'critical' ? 'error' : 'warning'}
                  icon={getAlertIcon(alert.severity)}
                  showIcon
                  closable
                />
              </Col>
            ))}
          </Row>
        </div>
      )}

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={16}>
          <Card title="Fraud Detection Trend (24 Hours)" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getFraudTrendData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <RechartsTooltip />
                <Line type="monotone" dataKey="total" stroke="#1890ff" name="Total Transactions" />
                <Line type="monotone" dataKey="fraud" stroke="#ff4d4f" name="Fraud Transactions" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="Transaction Distribution" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getFraudDistributionData()}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {getFraudDistributionData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <Space>
                <Tag color="#52c41a">Legitimate: 98.5%</Tag>
                <Tag color="#ff4d4f">Fraud: 1.5%</Tag>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Transaction Types and Recent Predictions */}
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="Transactions by Type" size="small">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={getTransactionTypeData()} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="type" type="category" width={80} />
                <RechartsTooltip />
                <Bar dataKey="count" fill="#1890ff" name="Total" />
                <Bar dataKey="fraud" fill="#ff4d4f" name="Fraud" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Performance Metrics" size="small">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Avg Response Time"
                  value={metrics.performance?.avg_prediction_latency_ms || 0}
                  precision={1}
                  suffix="ms"
                  valueStyle={{ 
                    color: (metrics.performance?.avg_prediction_latency_ms || 0) > 100 ? '#ff4d4f' : '#52c41a' 
                  }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Throughput"
                  value={metrics.performance?.predictions_per_second || 0}
                  precision={1}
                  suffix="/sec"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
            </Row>
            <div style={{ marginTop: '24px' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="Model Accuracy"
                    value={95.2}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="False Positive Rate"
                    value={2.8}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#faad14' }}
                  />
                </Col>
              </Row>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Recent Predictions Table */}
      <Card title="Recent Predictions" size="small" style={{ marginTop: '16px' }}>
        <Table
          columns={columns}
          dataSource={predictions}
          rowKey="transaction_id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;
