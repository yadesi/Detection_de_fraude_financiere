import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Button, Space, Typography, Card, Row, Col, Statistic } from 'antd';
import { 
  DashboardOutlined, 
  UploadOutlined, 
  BarChartOutlined, 
  SettingOutlined,
  SafetyOutlined,
  AlertOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined
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
  const [systemHealth, setSystemHealth] = useState({});
  const [stats, setStats] = useState({
    totalPredictions: 0,
    fraudRate: 0,
    avgLatency: 0,
    throughput: 0
  });

  useEffect(() => {
    // Fetch system health and stats periodically
    const fetchSystemData = async () => {
      try {
        const healthResponse = await fetch('http://localhost:8000/health');
        const healthData = await healthResponse.json();
        setSystemHealth(healthData);

        const metricsResponse = await fetch('http://localhost:8000/metrics');
        const metricsData = await metricsResponse.json();
        
        if (metricsData.prediction_stats) {
          setStats({
            totalPredictions: metricsData.prediction_stats.total_predictions || 0,
            fraudRate: (metricsData.prediction_stats.fraud_rate * 100) || 0,
            avgLatency: metricsData.performance?.avg_prediction_latency_ms || 0,
            throughput: metricsData.performance?.predictions_per_second || 0
          });
        }
      } catch (error) {
        console.error('Failed to fetch system data:', error);
      }
    };

    fetchSystemData();
    const interval = setInterval(fetchSystemData, 30000); // Update every 30 seconds

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
      key: '/manual',
      icon: <SafetyOutlined />,
      label: <Link to="/manual">Manual Entry</Link>,
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

  const getSystemStatusColor = () => {
    const services = systemHealth.services || {};
    const allHealthy = Object.values(services).every(service => 
      service.status === 'connected' || service.status === 'healthy'
    );
    return allHealthy ? '#52c41a' : '#ff4d4f';
  };

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          style={{
            background: '#001529',
          }}
        >
          <div style={{ 
            padding: '16px', 
            textAlign: 'center',
            borderBottom: '1px solid #303030'
          }}>
            <SafetyOutlined style={{ 
              fontSize: '24px', 
              color: '#1890ff',
              marginBottom: '8px'
            }} />
            <Title 
              level={4} 
              style={{ 
                color: 'white', 
                margin: 0,
                fontSize: collapsed ? '14px' : '16px'
              }}
            >
              {collapsed ? 'FD' : 'Fraud Detection'}
            </Title>
          </div>
          
          <Menu
            theme="dark"
            mode="inline"
            defaultSelectedKeys={['/']}
            items={menuItems}
            style={{ borderRight: 0 }}
          />
        </Sider>
        
        <Layout>
          <Header style={{ 
            padding: '0 16px', 
            background: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
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
            
            <Space align="center">
              <Space>
                <div style={{ textAlign: 'right' }}>
                  <Text type="secondary">System Status</Text>
                  <div>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      backgroundColor: getSystemStatusColor(),
                      display: 'inline-block',
                      marginRight: '8px'
                    }} />
                    <Text strong>
                      {systemHealth.status === 'healthy' ? 'Healthy' : 'Warning'}
                    </Text>
                  </div>
                </div>
              </Space>
            </Space>
          </Header>
          
          <Content style={{ 
            margin: '16px',
            padding: '24px',
            background: '#fff',
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)'
          }}>
            {/* Stats Overview */}
            <Row gutter={16} style={{ marginBottom: '24px' }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Total Predictions"
                    value={stats.totalPredictions}
                    prefix={<SafetyOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Fraud Rate"
                    value={stats.fraudRate}
                    precision={2}
                    suffix="%"
                    prefix={<AlertOutlined />}
                    valueStyle={{ 
                      color: stats.fraudRate > 5 ? '#ff4d4f' : '#52c41a' 
                    }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Avg Latency"
                    value={stats.avgLatency}
                    precision={1}
                    suffix="ms"
                    valueStyle={{ 
                      color: stats.avgLatency > 100 ? '#ff4d4f' : '#52c41a' 
                    }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Throughput"
                    value={stats.throughput}
                    precision={1}
                    suffix="/s"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
            </Row>
            
            {/* Main Content */}
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<FileUpload />} />
              <Route path="/manual" element={<TransactionForm />} />
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
