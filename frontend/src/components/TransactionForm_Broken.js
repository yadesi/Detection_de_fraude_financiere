import React, { useState } from 'react';
import { 
  Form, 
  Input, 
  Select, 
  Button, 
  Card, 
  Row, 
  Col, 
  Alert, 
  Statistic, 
  Progress, 
  Tag, 
  Space,
  Typography,
  Divider,
  List,
  Badge
} from 'antd';
import { 
  SafetyOutlined, 
  SendOutlined, 
  ClearOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  DollarOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const TransactionForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);

  const handleSubmit = async (values) => {
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await fetch('http://localhost:8000/predict/single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        const result = await response.json();
        setPrediction(result);
        
        // Add to recent transactions
        const newTransaction = {
          ...values,
          prediction: result.prediction,
          timestamp: new Date().toISOString(),
          id: `TXN_${Date.now()}`
        };
        setRecentTransactions(prev => [newTransaction, ...prev.slice(0, 4)]);
        
        // Clear form
        form.resetFields();
      } else {
        throw new Error('Prediction failed');
      }
    } catch (err) {
      setError('Failed to process transaction. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPredictionColor = (isFraud) => {
    return isFraud ? '#ff4d4f' : '#52c41a';
  };

  const getPredictionTag = (isFraud) => {
    return isFraud ? 'FRAUD' : 'LEGITIMATE';
  };

  const getRiskLevel = (probability) => {
    if (probability > 0.7) return { level: 'danger', text: 'High Risk' };
    if (probability > 0.3) return { level: 'warning', text: 'Medium Risk' };
    return { level: 'success', text: 'Low Risk' };
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[24, 24]}>
        {/* Transaction Form */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <SafetyOutlined />
                <span>Manual Transaction Entry</span>
              </Space>
            }
            extra={
              <Button 
                icon={<ClearOutlined />} 
                onClick={() => form.resetFields()}
              >
                Clear
              </Button>
            }
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{
                type: 'TRANSFER',
                amount: 1000,
                oldbalanceOrg: 10000,
                newbalanceOrig: 9000,
                oldbalanceDest: 5000,
                newbalanceDest: 6000
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Transaction ID"
                    name="transaction_id"
                    rules={[{ required: true, message: 'Please enter transaction ID' }]}
                  >
                    <Input 
                      placeholder="e.g., TXN_001" 
                      prefix={<ClockCircleOutlined />}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Transaction Type"
                    name="type"
                    rules={[{ required: true, message: 'Please select transaction type' }]}
                  >
                    <Select placeholder="Select type">
                      <Option value="CASH-IN">CASH-IN</Option>
                      <Option value="CASH-OUT">CASH-OUT</Option>
                      <Option value="TRANSFER">TRANSFER</Option>
                      <Option value="PAYMENT">PAYMENT</Option>
                      <Option value="DEBIT">DEBIT</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Amount"
                    name="amount"
                    rules={[{ required: true, message: 'Please enter amount' }]}
                  >
                    <Input
                      type="number"
                      placeholder="0.00"
                      prefix={<DollarOutlined />}
                      addonAfter="USD"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Origin Account"
                    name="nameOrig"
                    rules={[{ required: true, message: 'Please enter origin account' }]}
                  >
                    <Input placeholder="e.g., C123456789" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Origin Balance (Before)"
                    name="oldbalanceOrg"
                    rules={[{ required: true, message: 'Please enter origin balance' }]}
                  >
                    <Input
                      type="number"
                      placeholder="0.00"
                      prefix={<DollarOutlined />}
                      addonAfter="USD"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Origin Balance (After)"
                    name="newbalanceOrig"
                    rules={[{ required: true, message: 'Please enter new origin balance' }]}
                  >
                    <Input
                      type="number"
                      placeholder="0.00"
                      prefix={<DollarOutlined />}
                      addonAfter="USD"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Destination Account"
                    name="nameDest"
                    rules={[{ required: true, message: 'Please enter destination account' }]}
                  >
                    <Input placeholder="e.g., M987654321" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Destination Balance (Before)"
                    name="oldbalanceDest"
                    rules={[{ required: true, message: 'Please enter destination balance' }]}
                  >
                    <Input
                      type="number"
                      placeholder="0.00"
                      prefix={<DollarOutlined />}
                      addonAfter="USD"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="Destination Balance (After)"
                name="newbalanceDest"
                rules={[{ required: true, message: 'Please enter new destination balance' }]}
              >
                <Input
                  type="number"
                  placeholder="0.00"
                  prefix={<DollarOutlined />}
                  addonAfter="USD"
                />
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  icon={<SendOutlined />}
                  size="large"
                  style={{ width: '100%' }}
                >
                  {loading ? 'Processing...' : 'Analyze Transaction'}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Results Panel */}
        <Col xs={24} lg={12}>
          {/* Prediction Result */}
          {prediction && (
            <Card 
              title="Prediction Result"
              style={{ marginBottom: 16 }}
              extra={
                <Badge 
                  status={prediction.prediction.is_fraud ? 'error' : 'success'}
                  text={getPredictionTag(prediction.prediction.is_fraud)}
                />
              }
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="Fraud Probability"
                    value={prediction.prediction.fraud_probability * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ 
                      color: getPredictionColor(prediction.prediction.is_fraud),
                      fontSize: '24px',
                      fontWeight: 'bold'
                    }}
                  />
                  <Progress
                    percent={prediction.prediction.fraud_probability * 100}
                    status={prediction.prediction.fraud_probability > 0.7 ? 'exception' : 
                           prediction.prediction.fraud_probability > 0.3 ? 'active' : 'success'}
                    showInfo={false}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Model Confidence"
                    value={prediction.prediction.confidence * 100}
                    precision={1}
                    suffix="%"
                    valueStyle={{ 
                      color: '#1890ff',
                      fontSize: '24px',
                      fontWeight: 'bold'
                    }}
                  />
                  <Progress
                    percent={prediction.prediction.confidence * 100}
                    status="active"
                    showInfo={false}
                  />
                </Col>
              </Row>
              
              <Divider />
              
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>Transaction ID:</Text>
                  <Text code> {prediction.transaction_id}</Text>
                </div>
                <div>
                  <Text strong>Processing Time:</Text>
                  <Text> {prediction.latency_ms}ms</Text>
                </div>
                <div>
                  <Text strong>Risk Level:</Text>
                  <Tag color={getRiskLevel(prediction.prediction.fraud_probability).level}>
                    {getRiskLevel(prediction.prediction.fraud_probability).text}
                  </Tag>
                </div>
              </Space>
            </Card>
          )}

          {/* Error Alert */}
          {error && (
            <Alert
              message="Error"
              description={error}
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* Recent Transactions */}
          <Card 
            title="Recent Transactions"
            extra={<Badge count={recentTransactions.length} />}
          >
            {recentTransactions.length > 0 ? (
              <List
                dataSource={recentTransactions}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        item.prediction.is_fraud ? 
                          <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: '20px' }} /> :
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '20px' }} />
                      }
                      title={
                        <Space>
                          <Text code>{item.id}</Text>
                          <Tag color={item.prediction.is_fraud ? 'red' : 'green'}>
                            {getPredictionTag(item.prediction.is_fraud)}
                          </Tag>
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size="small">
                          <Text type="secondary">
                            {item.type} - ${item.amount.toLocaleString()}
                          </Text>
                          <Progress
                            percent={item.prediction.fraud_probability * 100}
                            size="small"
                            status={item.prediction.fraud_probability > 0.7 ? 'exception' : 
                                   item.prediction.fraud_probability > 0.3 ? 'active' : 'success'}
                            format={() => `${(item.prediction.fraud_probability * 100).toFixed(1)}%`}
                          />
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
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

export default TransactionForm;
