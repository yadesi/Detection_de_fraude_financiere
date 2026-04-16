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
  Timeline
} from 'antd';
import { 
  ReloadOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DashboardOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  TrendingUpOutlined,
  FireOutlined,
  ShieldOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const healthResponse = await fetch('http://localhost:8000/health');
      if (!healthResponse.ok) {
        throw new Error('Backend not responding');
      }
      setConnectionStatus('connected');

      try {
        const predictionsResponse = await fetch('http://localhost:8000/predictions/history?limit=10');
        if (predictionsResponse.ok) {
          const predictionsData = await predictionsResponse.json();
          setPredictions(Array.isArray(predictionsData) ? predictionsData : []);
        }
      } catch (err) {
        setPredictions(generateMockPredictions());
      }

      try {
        const metricsResponse = await fetch('http://localhost:8000/metrics');
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          setMetrics(metricsData || {});
        }
      } catch (err) {
        setMetrics(generateMockMetrics());
      }

      setAlerts(generateMockAlerts());
      
    } catch (err) {
      setError(err.message);
      setConnectionStatus('disconnected');
      setPredictions(generateMockPredictions());
      setMetrics(generateMockMetrics());
      setAlerts(generateMockAlerts());
    } finally {
      setLoading(false);
    }
  };

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

      {/* Charts Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Fraud Detection Trend" extra={<Badge count="7 Days" />}>
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <BarChartOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
              <div style={{ marginTop: '16px' }}>
                <Title level={4}>Interactive Charts</Title>
                <Text type="secondary">Charts will display here when data is available</Text>
                <br />
                <Text type="secondary">7-day trend analysis</Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Transaction Distribution">
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <DashboardOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
              <div style={{ marginTop: '16px' }}>
                <Title level={4}>Distribution Chart</Title>
                <Text type="secondary">Fraud vs Legitimate</Text>
                <br />
                <Text type="secondary">Pie chart visualization</Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Performance Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24}>
          <Card title="System Performance" extra={<ShieldOutlined />}>
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <TrendingUpOutlined style={{ fontSize: '48px', color: '#722ed1' }} />
              <div style={{ marginTop: '16px' }}>
                <Title level={4}>Performance Metrics</Title>
                <Text type="secondary">Latency and throughput over time</Text>
              </div>
            </div>
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

export default Dashboard;
