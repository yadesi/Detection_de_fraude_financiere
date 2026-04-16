import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Button, Typography, Card, Row, Col, Statistic, Space } from 'antd';
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
  TrophyOutlined
} from '@ant-design/icons';
import Dashboard from './components/Dashboard';
import FileUpload from './components/FileUpload';
import TransactionForm from './components/TransactionForm';
import Analytics from './components/Analytics';
import Settings from './components/Settings';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [stats, setStats] = useState({
    totalPredictions: 15420,
    fraudRate: 4.98,
    avgLatency: 45.2,
    throughput: 156.8
  });
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    const fetchSystemData = async () => {
      try {
        const healthResponse = await fetch('http://localhost:8000/health');
        const healthData = await healthResponse.json();
        setConnectionStatus('connected');

        const metricsResponse = await fetch('http://localhost:8000/metrics');
        const metricsData = await metricsResponse.json();
        
        if (metricsData.prediction_stats) {
          setStats({
            totalPredictions: metricsData.prediction_stats.total_predictions || 15420,
            fraudRate: (metricsData.prediction_stats.fraud_rate * 100) || 4.98,
            avgLatency: metricsData.performance?.avg_prediction_latency_ms || 45.2,
            throughput: metricsData.performance?.predictions_per_second || 156.8
          });
        }
      } catch (error) {
        console.log('Backend not available, using mock data');
        setConnectionStatus('disconnected');
        setStats({
          totalPredictions: 15420,
          fraudRate: 4.98,
          avgLatency: 45.2,
          throughput: 156.8
        });
      }
    };

    fetchSystemData();
    const interval = setInterval(fetchSystemData, 30000);
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

  const getConnectionBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return <span style={{ color: '#52c41a', fontWeight: 'bold' }}>Connected</span>;
      case 'disconnected':
        return <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>Demo Mode</span>;
      default:
        return <span style={{ color: '#1890ff', fontWeight: 'bold' }}>Connecting...</span>;
    }
  };

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
              {getConnectionBadge()}
            </Space>
          </Header>
          
          <Content style={{ 
            margin: '16px',
            padding: 0,
            background: '#f5f5f5',
            minHeight: 280 
          }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<FileUpload />} />
              <Route path="/transaction" element={<TransactionForm />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
