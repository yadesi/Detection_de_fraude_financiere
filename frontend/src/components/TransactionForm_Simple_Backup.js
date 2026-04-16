import React, { useState } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Button, 
  Row, 
  Col, 
  Alert, 
  Space,
  Typography,
  Statistic,
  Tag,
  Progress,
  Divider,
  Tooltip
} from 'antd';
import { 
  SendOutlined, 
  CheckCircleOutlined, 
  WarningOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const TransactionForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const onFinish = async (values) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Add timestamp if not provided
      const transactionData = {
        ...values,
        transaction_id: values.transaction_id || `TXN_${Date.now()}`,
        timestamp: values.timestamp || new Date().toISOString()
      };

      const response = await fetch('http://localhost:8000/predict/single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactionData)
      });

      if (!response.ok) {
        throw new Error(`Prediction failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      
    } catch (err) {
      console.error('Prediction error:', err);
      setError(err.message || 'Failed to process transaction');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (probability) => {
    if (probability > 0.8) return { level: 'Very High', color: '#ff4d4f', icon: <WarningOutlined /> };
    if (probability > 0.6) return { level: 'High', color: '#ff7875', icon: <WarningOutlined /> };
    if (probability > 0.4) return { level: 'Medium', color: '#faad14', icon: <InfoCircleOutlined /> };
    if (probability > 0.2) return { level: 'Low', color: '#52c41a', icon: <CheckCircleOutlined /> };
    return { level: 'Very Low', color: '#52c41a', icon: <CheckCircleOutlined /> };
  };

  const getFeatureAnalysis = (values) => {
    const features = [];
    
    // Amount analysis
    if (values.amount > 10000) {
      features.push({ name: 'High Amount', impact: 'positive', description: 'Large transactions are more suspicious' });
    }
    
    // Transaction type analysis
    if (['TRANSFER', 'CASH-OUT'].includes(values.type)) {
      features.push({ name: 'High Risk Type', impact: 'positive', description: 'Transfers and cash-outs are higher risk' });
    }
    
    // Balance analysis
    const balanceChange = values.newbalanceOrig - values.oldbalanceOrg;
    if (Math.abs(balanceChange - values.amount) > 0.01 && values.amount > 0) {
      features.push({ name: 'Balance Mismatch', impact: 'positive', description: 'Balance change doesn\'t match transaction amount' });
    }
    
    // Time analysis
    const hour = new Date().getHours();
    if (hour < 6 || hour > 22) {
      features.push({ name: 'Unusual Time', impact: 'positive', description: 'Transaction during unusual hours' });
    }
    
    return features;
  };

  return (
    <div>
      <Title level={2}>Manual Transaction Entry</Title>
      
      <Row gutter={24}>
        <Col span={14}>
          <Card title="Transaction Details">
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              initialValues={{
                type: 'TRANSFER',
                oldbalanceOrg: 10000,
                newbalanceOrig: 5000,
                oldbalanceDest: 5000,
                newbalanceDest: 10000,
                amount: 5000
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Transaction ID"
                    name="transaction_id"
                    tooltip="Optional - will be auto-generated if not provided"
                  >
                    <Input placeholder="TXN_123456" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Transaction Type"
                    name="type"
                    rules={[{ required: true, message: 'Please select transaction type!' }]}
                  >
                    <Select placeholder="Select transaction type">
                      <Option value="CASH-IN">CASH-IN</Option>
                      <Option value="CASH-OUT">CASH-OUT</Option>
                      <Option value="DEBIT">DEBIT</Option>
                      <Option value="PAYMENT">PAYMENT</Option>
                      <Option value="TRANSFER">TRANSFER</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Amount ($)"
                    name="amount"
                    rules={[
                      { required: true, message: 'Please enter amount!' },
                      { type: 'number', min: 0.01, message: 'Amount must be positive!' }
                    ]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      placeholder="0.00"
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Origin Account"
                    name="nameOrig"
                    rules={[{ required: true, message: 'Please enter origin account!' }]}
                  >
                    <Input placeholder="C123456789" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Origin Balance (Before)"
                    name="oldbalanceOrg"
                    rules={[{ required: true, message: 'Please enter origin balance!' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      placeholder="0.00"
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Origin Balance (After)"
                    name="newbalanceOrig"
                    rules={[{ required: true, message: 'Please enter new origin balance!' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      placeholder="0.00"
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Destination Account"
                    name="nameDest"
                    rules={[{ required: true, message: 'Please enter destination account!' }]}
                  >
                    <Input placeholder="M123456789" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Destination Balance (Before)"
                    name="oldbalanceDest"
                    rules={[{ required: true, message: 'Please enter destination balance!' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      placeholder="0.00"
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Destination Balance (After)"
                    name="newbalanceDest"
                    rules={[{ required: true, message: 'Please enter new destination balance!' }]}
                  >
                    <InputNumber
                      style={{ width: '100%' }}
                      placeholder="0.00"
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Timestamp"
                    name="timestamp"
                    tooltip="Optional - will use current time if not provided"
                  >
                    <Input placeholder="2024-01-01T12:00:00Z" />
                  </Form.Item>
                </Col>
              </Row>

              {error && (
                <Alert
                  message="Processing Error"
                  description={error}
                  type="error"
                  showIcon
                  closable
                  style={{ marginBottom: '16px' }}
                />
              )}

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<SendOutlined />}
                  size="large"
                >
                  {loading ? 'Analyzing...' : 'Analyze Transaction'}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={10}>
          {result ? (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* Result Summary */}
              <Card title="Analysis Result">
                <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                  <Tag 
                    color={result.prediction.is_fraud ? 'red' : 'green'}
                    style={{ fontSize: '16px', padding: '8px 16px' }}
                  >
                    {result.prediction.is_fraud ? 'FRAUD DETECTED' : 'LEGITIMATE'}
                  </Tag>
                </div>

                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Fraud Probability"
                      value={result.prediction.fraud_probability * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{ 
                        color: result.prediction.fraud_probability > 0.5 ? '#ff4d4f' : '#52c41a' 
                      }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Confidence"
                      value={result.prediction.confidence * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                </Row>

                <Divider />

                <div>
                  <Text strong>Risk Level: </Text>
                  <Tag 
                    color={getRiskLevel(result.prediction.fraud_probability).color}
                    icon={getRiskLevel(result.prediction.fraud_probability).icon}
                  >
                    {getRiskLevel(result.prediction.fraud_probability).level}
                  </Tag>
                </div>

                <div style={{ marginTop: '16px' }}>
                  <Text strong>Fraud Score: </Text>
                  <Progress
                    percent={result.prediction.fraud_probability * 100}
                    status={result.prediction.fraud_probability > 0.7 ? 'exception' : 'normal'}
                    strokeColor={result.prediction.fraud_probability > 0.7 ? '#ff4d4f' : '#52c41a'}
                  />
                </div>
              </Card>

              {/* Feature Analysis */}
              <Card title="Feature Analysis">
                {form.getFieldsValue() && (
                  <div>
                    {getFeatureAnalysis(form.getFieldsValue()).map((feature, index) => (
                      <div key={index} style={{ marginBottom: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Tag color={feature.impact === 'positive' ? 'red' : 'green'}>
                            {feature.impact === 'positive' ? 'Risk Factor' : 'Safe Indicator'}
                          </Tag>
                          <Text strong>{feature.name}</Text>
                        </div>
                        <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
                          {feature.description}
                        </Text>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* Model Info */}
              <Card title="Model Information">
                <Row gutter={16}>
                  <Col span={24}>
                    <Statistic
                      title="Model Version"
                      value={result.model_version || 'Latest'}
                      prefix={<InfoCircleOutlined />}
                    />
                  </Col>
                </Row>
                <Row gutter={16} style={{ marginTop: '16px' }}>
                  <Col span={12}>
                    <Statistic
                      title="Processing Time"
                      value={result.latency_ms}
                      precision={1}
                      suffix="ms"
                      valueStyle={{ 
                        color: result.latency_ms > 100 ? '#ff4d4f' : '#52c41a' 
                      }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Analysis Time"
                      value={new Date(result.prediction_timestamp).toLocaleTimeString()}
                      prefix={<CheckCircleOutlined />}
                    />
                  </Col>
                </Row>
              </Card>
            </Space>
          ) : (
            <Card title="Analysis Results">
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <InfoCircleOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
                <div>
                  <Text type="secondary">
                    Enter transaction details and click "Analyze Transaction" to see fraud detection results
                  </Text>
                </div>
              </div>
            </Card>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default TransactionForm;
