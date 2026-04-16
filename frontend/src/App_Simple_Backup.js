import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Button, Typography, Card, Row, Col, Statistic } from 'antd';
import { 
  DashboardOutlined, 
  UploadOutlined, 
  BarChartOutlined, 
  SettingOutlined,
  SafetyOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined
} from '@ant-design/icons';

// Simple components to avoid import errors
const SimpleDashboard = () => {
  const [data, setData] = useState({
    totalPredictions: 15420,
    fraudRate: 4.98,
    avgLatency: 45.2,
    throughput: 156.8
  });

  useEffect(() => {
    // Simulate data fetching
    const interval = setInterval(() => {
      setData(prev => ({
        ...prev,
        totalPredictions: prev.totalPredictions + Math.floor(Math.random() * 10),
        avgLatency: 40 + Math.random() * 20
      }));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Predictions"
              value={data.totalPredictions}
              prefix={<DashboardOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Fraud Rate"
              value={data.fraudRate}
              suffix="%"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Latency"
              value={data.avgLatency}
              suffix="ms"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Throughput"
              value={data.throughput}
              suffix="/sec"
            />
          </Card>
        </Col>
      </Row>
      
      <Row style={{ marginTop: '24px' }}>
        <Col span={24}>
          <Card title="Recent Activity">
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <h3>Dashboard is working!</h3>
              <p>Real-time fraud detection system is operational.</p>
              <p>Total predictions processed: {data.totalPredictions.toLocaleString()}</p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

const SimpleUpload = () => (
  <div style={{ padding: '24px' }}>
    <Card title="File Upload">
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h3>Upload Transaction Files</h3>
        <p>Upload CSV or JSON files for fraud detection analysis.</p>
        <Button type="primary" size="large">Choose File</Button>
      </div>
    </Card>
  </div>
);

const SimpleTransaction = () => (
  <div style={{ padding: '24px' }}>
    <Card title="Manual Transaction Entry">
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h3>Enter Transaction Details</h3>
        <p>Manually enter transaction data for fraud analysis.</p>
        <Button type="primary" size="large">Add Transaction</Button>
      </div>
    </Card>
  </div>
);

const SimpleAnalytics = () => (
  <div style={{ padding: '24px' }}>
    <Card title="Analytics Dashboard">
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h3>Analytics & Insights</h3>
        <p>View detailed analytics and fraud patterns.</p>
        <Button type="primary" size="large">View Analytics</Button>
      </div>
    </Card>
  </div>
);

const SimpleSettings = () => (
  <div style={{ padding: '24px' }}>
    <Card title="System Settings">
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <h3>Configure System</h3>
        <p>Adjust system parameters and settings.</p>
        <Button type="primary" size="large">Open Settings</Button>
      </div>
    </Card>
  </div>
);

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);

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
        <Sider trigger={null} collapsible collapsed={collapsed}>
          <div style={{ 
            padding: '16px', 
            textAlign: 'center',
            borderBottom: '1px solid #f0f0f0'
          }}>
            <Title level={4} style={{ color: '#fff', margin: 0 }}>
              {collapsed ? 'FD' : 'Fraud Detection'}
            </Title>
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[window.location.pathname]}
            items={menuItems}
          />
        </Sider>
        
        <Layout>
          <Header style={{ 
            padding: '0 16px', 
            background: '#fff',
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
            
            <div>
              <Title level={4} style={{ margin: 0 }}>
                Fraud Detection System
              </Title>
            </div>
          </Header>
          
          <Content style={{ 
            margin: '16px',
            padding: 0,
            background: '#f0f2f5',
            minHeight: 280 
          }}>
            <Routes>
              <Route path="/" element={<SimpleDashboard />} />
              <Route path="/upload" element={<SimpleUpload />} />
              <Route path="/transaction" element={<SimpleTransaction />} />
              <Route path="/analytics" element={<SimpleAnalytics />} />
              <Route path="/settings" element={<SimpleSettings />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
