import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Select, 
  DatePicker, 
  Button, 
  Space,
  Typography,
  Statistic,
  Table,
  Tag,
  Alert
} from 'antd';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ScatterChart,
  Scatter
} from 'recharts';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const Analytics = () => {
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState([
    moment().subtract(7, 'days'),
    moment()
  ]);
  const [transactionType, setTransactionType] = useState('all');
  const [analyticsData, setAnalyticsData] = useState({});

  useEffect(() => {
    fetchAnalyticsData();
  }, [dateRange, transactionType]);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would call the analytics API
      // For now, we'll generate sample data
      const sampleData = generateSampleAnalyticsData();
      setAnalyticsData(sampleData);
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateSampleAnalyticsData = () => {
    // Generate time series data
    const timeSeriesData = [];
    for (let i = 6; i >= 0; i--) {
      const date = moment().subtract(i, 'days');
      timeSeriesData.push({
        date: date.format('YYYY-MM-DD'),
        total: Math.floor(Math.random() * 1000) + 500,
        fraud: Math.floor(Math.random() * 50) + 10,
        legitimate: Math.floor(Math.random() * 950) + 450,
        fraudRate: ((Math.random() * 5) + 1).toFixed(2)
      });
    }

    // Generate hourly pattern data
    const hourlyData = [];
    for (let i = 0; i < 24; i++) {
      hourlyData.push({
        hour: i,
        volume: Math.floor(Math.random() * 100) + 50,
        fraudRate: ((Math.random() * 8) + 1).toFixed(2),
        avgAmount: Math.floor(Math.random() * 5000) + 1000
      });
    }

    // Generate transaction type distribution
    const typeDistribution = [
      { type: 'CASH-IN', count: 450, fraud: 9, amount: 2250000 },
      { type: 'CASH-OUT', count: 380, fraud: 38, amount: 1900000 },
      { type: 'TRANSFER', count: 220, fraud: 22, amount: 1100000 },
      { type: 'PAYMENT', count: 680, fraud: 7, amount: 3400000 },
      { type: 'DEBIT', count: 180, fraud: 2, amount: 900000 }
    ];

    // Generate amount distribution data
    const amountDistribution = [
      { range: '$0-$100', legitimate: 450, fraud: 5 },
      { range: '$100-$1K', legitimate: 380, fraud: 12 },
      { range: '$1K-$10K', legitimate: 220, fraud: 25 },
      { range: '$10K-$50K', legitimate: 68, fraud: 15 },
      { range: '$50K+', legitimate: 18, fraud: 8 }
    ];

    // Generate risk score distribution
    const riskDistribution = [
      { score: '0-0.2', count: 850 },
      { score: '0.2-0.4', count: 120 },
      { score: '0.4-0.6', count: 45 },
      { score: '0.6-0.8', count: 25 },
      { score: '0.8-1.0', count: 15 }
    ];

    // Generate top fraud patterns
    const fraudPatterns = [
      { pattern: 'High amount + unusual time', count: 45, percentage: 35.2 },
      { pattern: 'Balance mismatch', count: 28, percentage: 21.9 },
      { pattern: 'New account + large transfer', count: 22, percentage: 17.2 },
      { pattern: 'Multiple rapid transfers', count: 18, percentage: 14.1 },
      { pattern: 'Unusual destination', count: 15, percentage: 11.7 }
    ];

    return {
      timeSeriesData,
      hourlyData,
      typeDistribution,
      amountDistribution,
      riskDistribution,
      fraudPatterns,
      summary: {
        totalTransactions: timeSeriesData.reduce((sum, d) => sum + d.total, 0),
        totalFraud: timeSeriesData.reduce((sum, d) => sum + d.fraud, 0),
        avgFraudRate: (timeSeriesData.reduce((sum, d) => sum + parseFloat(d.fraudRate), 0) / timeSeriesData.length).toFixed(2),
        totalAmount: typeDistribution.reduce((sum, d) => sum + d.amount, 0)
      }
    };
  };

  const getFraudPatternsColumns = () => [
    {
      title: 'Fraud Pattern',
      dataIndex: 'pattern',
      key: 'pattern',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      render: (count) => <Tag color="red">{count}</Tag>
    },
    {
      title: 'Percentage',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (percentage) => `${percentage}%`
    }
  ];

  const COLORS = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1'];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Analytics & Insights</Title>
        <Space>
          <Button icon={<DownloadOutlined />}>Export Report</Button>
          <Button icon={<ReloadOutlined />} onClick={fetchAnalyticsData} loading={loading}>
            Refresh
          </Button>
        </Space>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <Text strong>Date Range:</Text>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              style={{ marginLeft: '8px', width: '100%' }}
            />
          </Col>
          <Col span={6}>
            <Text strong>Transaction Type:</Text>
            <Select
              value={transactionType}
              onChange={setTransactionType}
              style={{ marginLeft: '8px', width: '100%' }}
            >
              <Option value="all">All Types</Option>
              <Option value="CASH-IN">CASH-IN</Option>
              <Option value="CASH-OUT">CASH-OUT</Option>
              <Option value="TRANSFER">TRANSFER</Option>
              <Option value="PAYMENT">PAYMENT</Option>
              <Option value="DEBIT">DEBIT</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Transactions"
              value={analyticsData.summary?.totalTransactions || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Fraudulent Transactions"
              value={analyticsData.summary?.totalFraud || 0}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Average Fraud Rate"
              value={analyticsData.summary?.avgFraudRate || 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Amount"
              value={analyticsData.summary?.totalAmount || 0}
              precision={0}
              prefix="$"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Row 1 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={16}>
          <Card title="Transaction Volume Trend">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={analyticsData.timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Area type="monotone" dataKey="total" stackId="1" stroke="#1890ff" fill="#1890ff" />
                <Area type="monotone" dataKey="fraud" stackId="2" stroke="#ff4d4f" fill="#ff4d4f" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Transaction Types">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.typeDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {analyticsData.typeDistribution?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Charts Row 2 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <Card title="Hourly Fraud Pattern">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData.hourlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <RechartsTooltip />
                <Line yAxisId="left" type="monotone" dataKey="volume" stroke="#1890ff" name="Volume" />
                <Line yAxisId="right" type="monotone" dataKey="fraudRate" stroke="#ff4d4f" name="Fraud Rate %" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Risk Score Distribution">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.riskDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="score" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="count" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Charts Row 3 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card title="Amount Distribution Analysis">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.amountDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="legitimate" fill="#52c41a" name="Legitimate" />
                <Bar dataKey="fraud" fill="#ff4d4f" name="Fraud" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Fraud Patterns Table */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="Top Fraud Patterns">
            <Table
              columns={getFraudPatternsColumns()}
              dataSource={analyticsData.fraudPatterns}
              pagination={false}
              size="small"
              rowKey="pattern"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Key Insights">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Alert
                message="Peak Fraud Hours"
                description="Highest fraud rates detected between 2 AM - 6 AM"
                type="warning"
                showIcon
              />
              <Alert
                message="High-Risk Transaction Types"
                description="CASH-OUT and TRANSFER transactions show 3x higher fraud rates"
                type="error"
                showIcon
              />
              <Alert
                message="Amount Threshold"
                description="Transactions above $10,000 have 5x higher fraud probability"
                type="info"
                showIcon
              />
              <Alert
                message="Model Performance"
                description="Current model accuracy: 95.2% with 2.8% false positive rate"
                type="success"
                showIcon
              />
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Analytics;
