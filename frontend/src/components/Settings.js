import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  InputNumber, 
  Switch, 
  Button, 
  Space,
  Typography,
  Divider,
  Select,
  Slider,
  Alert,
  Row,
  Col,
  Statistic,
  Tag,
  Modal,
  message
} from 'antd';
import { 
  SaveOutlined, 
  ReloadOutlined, 
  SettingOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const Settings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [modelSettings, setModelSettings] = useState({});
  const [systemSettings, setSystemSettings] = useState({});
  const [retrainModalVisible, setRetrainModalVisible] = useState(false);
  const [retrainLoading, setRetrainLoading] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      // Fetch model info
      const modelResponse = await fetch('http://localhost:8000/model/info');
      const modelData = await modelResponse.json();
      setModelSettings(modelData);

      // Set default form values
      form.setFieldsValue({
        fraud_threshold: 0.5,
        confidence_threshold: 0.7,
        batch_size: 100,
        max_latency_ms: 100,
        auto_retrain: false,
        alert_high_fraud_rate: true,
        alert_system_health: true,
        alert_model_performance: true,
        kafka_topic: 'fraud_predictions',
        redis_ttl: 3600,
        monitoring_interval: 30
      });
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const handleSave = async (values) => {
    setLoading(true);
    try {
      // In a real implementation, this would save settings to the backend
      console.log('Saving settings:', values);
      message.success('Settings saved successfully!');
    } catch (error) {
      message.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleRetrainModel = async () => {
    setRetrainLoading(true);
    try {
      const response = await fetch('http://localhost:8000/model/retrain', {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        message.success(`Model retraining started (Job ID: ${data.job_id})`);
        setRetrainModalVisible(false);
      } else {
        throw new Error('Failed to start retraining');
      }
    } catch (error) {
      message.error('Failed to start model retraining');
    } finally {
      setRetrainLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
    message.info('Settings reset to defaults');
  };

  const getModelStatusColor = (status) => {
    switch (status) {
      case 'loaded': return '#52c41a';
      case 'loading': return '#faad14';
      case 'error': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

  return (
    <div>
      <Title level={2}>System Settings</Title>
      
      <Row gutter={24}>
        <Col span={16}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* Model Settings */}
            <Card title="Model Configuration">
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSave}
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label="Fraud Detection Threshold"
                      name="fraud_threshold"
                      tooltip="Minimum probability to classify as fraud"
                      rules={[{ required: true, message: 'Please set fraud threshold!' }]}
                    >
                      <Slider
                        min={0}
                        max={1}
                        step={0.01}
                        marks={{
                          0: '0%',
                          0.25: '25%',
                          0.5: '50%',
                          0.75: '75%',
                          1: '100%'
                        }}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label="Confidence Threshold"
                      name="confidence_threshold"
                      tooltip="Minimum confidence for predictions"
                      rules={[{ required: true, message: 'Please set confidence threshold!' }]}
                    >
                      <Slider
                        min={0}
                        max={1}
                        step={0.01}
                        marks={{
                          0: '0%',
                          0.25: '25%',
                          0.5: '50%',
                          0.75: '75%',
                          1: '100%'
                        }}
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label="Batch Size"
                      name="batch_size"
                      rules={[{ required: true, message: 'Please set batch size!' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={1}
                        max={10000}
                        placeholder="100"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label="Max Latency (ms)"
                      name="max_latency_ms"
                      rules={[{ required: true, message: 'Please set max latency!' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={10}
                        max={10000}
                        placeholder="100"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />

                <Title level={4}>Performance Settings</Title>
                
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label="Kafka Topic"
                      name="kafka_topic"
                      rules={[{ required: true, message: 'Please set Kafka topic!' }]}
                    >
                      <Input placeholder="fraud_predictions" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label="Redis TTL (seconds)"
                      name="redis_ttl"
                      rules={[{ required: true, message: 'Please set Redis TTL!' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={60}
                        max={86400}
                        placeholder="3600"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label="Monitoring Interval (seconds)"
                      name="monitoring_interval"
                      rules={[{ required: true, message: 'Please set monitoring interval!' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={5}
                        max={300}
                        placeholder="30"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label="Log Level"
                      name="log_level"
                      rules={[{ required: true, message: 'Please select log level!' }]}
                    >
                      <Select placeholder="Select log level">
                        <Option value="DEBUG">DEBUG</Option>
                        <Option value="INFO">INFO</Option>
                        <Option value="WARNING">WARNING</Option>
                        <Option value="ERROR">ERROR</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />

                <Title level={4}>Alert Settings</Title>
                
                <Row gutter={16}>
                  <Col span={24}>
                    <Form.Item
                      name="alert_high_fraud_rate"
                      valuePropName="checked"
                    >
                      <Switch /> Alert on high fraud rate
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={24}>
                    <Form.Item
                      name="alert_system_health"
                      valuePropName="checked"
                    >
                      <Switch /> Alert on system health issues
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={24}>
                    <Form.Item
                      name="alert_model_performance"
                      valuePropName="checked"
                    >
                      <Switch /> Alert on model performance degradation
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />

                <Title level={4}>Automation</Title>
                
                <Row gutter={16}>
                  <Col span={24}>
                    <Form.Item
                      name="auto_retrain"
                      valuePropName="checked"
                    >
                      <Switch /> Enable automatic model retraining
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item>
                  <Space>
                    <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
                      Save Settings
                    </Button>
                    <Button onClick={handleReset} icon={<ReloadOutlined />}>
                      Reset to Defaults
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </Card>
          </Space>
        </Col>

        <Col span={8}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* Model Status */}
            <Card title="Model Status">
              <Space direction="vertical" style={{ width: '100%' }}>
                {modelSettings.models && Object.entries(modelSettings.models).map(([name, info]) => (
                  <div key={name} style={{ marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong>{name.replace('_', ' ').toUpperCase()}</Text>
                      <Tag color={getModelStatusColor(info.loaded ? 'loaded' : 'error')}>
                        {info.loaded ? 'Loaded' : 'Not Loaded'}
                      </Tag>
                    </div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Type: {info.type}
                    </Text>
                  </div>
                ))}
              </Space>
              
              <Divider />
              
              <Button 
                type="primary" 
                onClick={() => setRetrainModalVisible(true)}
                icon={<SettingOutlined />}
                block
              >
                Retrain Models
              </Button>
            </Card>

            {/* System Information */}
            <Card title="System Information">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic
                  title="Models Loaded"
                  value={modelSettings.models ? Object.keys(modelSettings.models).length : 0}
                  prefix={<CheckCircleOutlined />}
                />
                
                <Statistic
                  title="Last Updated"
                  value={modelSettings.last_updated ? new Date(modelSettings.last_updated).toLocaleString() : 'Unknown'}
                  prefix={<SettingOutlined />}
                />
                
                <Statistic
                  title="Active Training Jobs"
                  value={modelSettings.training_jobs ? modelSettings.training_jobs.length : 0}
                  prefix={<SettingOutlined />}
                />
              </Space>
            </Card>

            {/* Quick Actions */}
            <Card title="Quick Actions">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button block>Clear Model Cache</Button>
                <Button block>Export Model Config</Button>
                <Button block>Import Model Config</Button>
                <Button block danger>Reset All Models</Button>
              </Space>
            </Card>

            {/* System Health */}
            <Card title="System Health">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Alert
                  message="API Status"
                  description="All services operational"
                  type="success"
                  showIcon
                  size="small"
                />
                
                <Alert
                  message="Model Performance"
                  description="Accuracy above threshold"
                  type="success"
                  showIcon
                  size="small"
                />
                
                <Alert
                  message="Resource Usage"
                  description="CPU and Memory within limits"
                  type="warning"
                  showIcon
                  size="small"
                />
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>

      {/* Retrain Modal */}
      <Modal
        title="Model Retraining"
        open={retrainModalVisible}
        onCancel={() => setRetrainModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setRetrainModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="retrain" type="primary" loading={retrainLoading} onClick={handleRetrainModel}>
            Start Retraining
          </Button>
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="Retraining Information"
            description="This will start a background job to retrain all fraud detection models with the latest data. The process may take several minutes to complete."
            type="info"
            showIcon
          />
          
          <div>
            <Text strong>Models to be retrained:</Text>
            <ul style={{ marginTop: '8px' }}>
              <li>Isolation Forest</li>
              <li>XGBoost Classifier</li>
              <li>Ensemble Model</li>
            </ul>
          </div>
          
          <div>
            <Text strong>Estimated time:</Text> 15-30 minutes
          </div>
          
          <div>
            <Text strong>Impact:</Text> System will remain operational during retraining
          </div>
        </Space>
      </Modal>
    </div>
  );
};

export default Settings;
