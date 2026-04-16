import React, { useState } from 'react';
import { 
  Card, 
  Upload, 
  Button, 
  Progress, 
  Table, 
  Tag, 
  Alert, 
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Modal,
  Result
} from 'antd';
import { 
  InboxOutlined, 
  UploadOutlined, 
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const FileUpload = () => {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [showResults, setShowResults] = useState(false);

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.csv,.json',
    fileList,
    beforeUpload: (file) => {
      // Check file size (max 50MB)
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        setError('File must be smaller than 50MB!');
        return false;
      }

      // Check file type
      const isValidType = file.type === 'text/csv' || file.type === 'application/json' || file.name.endsWith('.csv') || file.name.endsWith('.json');
      if (!isValidType) {
        setError('Please upload CSV or JSON files only!');
        return false;
      }

      setFileList([file]);
      setError(null);
      return false; // Prevent automatic upload
    },
    onRemove: () => {
      setFileList([]);
      setResults(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (fileList.length === 0) {
      setError('Please select a file first!');
      return;
    }

    const file = fileList[0];
    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch('http://localhost:8000/predict/file', {
        method: 'POST',
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
      setShowResults(true);
      
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload and process file');
    } finally {
      setUploading(false);
    }
  };

  const getResultsColumns = () => [
    {
      title: 'Transaction ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 150,
      render: (text) => <Text code>{text}</Text>
    },
    {
      title: 'Fraud Probability',
      dataIndex: ['prediction', 'fraud_probability'],
      key: 'fraud_probability',
      width: 150,
      render: (probability) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ flex: 1 }}>
            <div 
              style={{
                height: '6px',
                backgroundColor: '#e0e0e0',
                borderRadius: '3px',
                overflow: 'hidden'
              }}
            >
              <div 
                style={{
                  height: '100%',
                  width: `${probability * 100}%`,
                  backgroundColor: probability > 0.7 ? '#ff4d4f' : probability > 0.3 ? '#faad14' : '#52c41a',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
          </div>
          <Text style={{ minWidth: '50px', textAlign: 'right' }}>
            {(probability * 100).toFixed(1)}%
          </Text>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: ['prediction', 'is_fraud'],
      key: 'is_fraud',
      width: 100,
      render: (isFraud) => (
        <Tag color={isFraud ? 'red' : 'green'}>
          {isFraud ? 'FRAUD' : 'LEGITIMATE'}
        </Tag>
      )
    },
    {
      title: 'Confidence',
      dataIndex: ['prediction', 'confidence'],
      key: 'confidence',
      width: 100,
      render: (confidence) => `${(confidence * 100).toFixed(1)}%`
    }
  ];

  const getFraudDistributionData = () => {
    if (!results?.predictions) return [];
    
    const fraudCount = results.predictions.filter(p => p.prediction.is_fraud).length;
    const legitimateCount = results.predictions.length - fraudCount;
    
    return [
      { name: 'Legitimate', value: legitimateCount, color: '#52c41a' },
      { name: 'Fraud', value: fraudCount, color: '#ff4d4f' }
    ];
  };

  const getFraudProbabilityDistribution = () => {
    if (!results?.predictions) return [];
    
    const ranges = [
      { range: '0-20%', min: 0, max: 0.2, count: 0 },
      { range: '20-40%', min: 0.2, max: 0.4, count: 0 },
      { range: '40-60%', min: 0.4, max: 0.6, count: 0 },
      { range: '60-80%', min: 0.6, max: 0.8, count: 0 },
      { range: '80-100%', min: 0.8, max: 1.0, count: 0 }
    ];
    
    results.predictions.forEach(p => {
      const prob = p.prediction.fraud_probability;
      const range = ranges.find(r => prob >= r.min && prob < r.max);
      if (range) range.count++;
    });
    
    return ranges.map(r => ({ probability: r.range, count: r.count }));
  };

  const getProcessingTimesData = () => {
    if (!results?.predictions) return [];
    
    // Generate sample processing time data
    return Array.from({ length: 10 }, (_, i) => ({
      batch: i + 1,
      time: Math.random() * 50 + 10 // 10-60ms
    }));
  };

  return (
    <div>
      <Title level={2}>File Upload & Analysis</Title>
      
      {/* Upload Section */}
      <Card title="Upload Transaction File" style={{ marginBottom: '24px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">
              Support for CSV and JSON files only. Maximum file size: 50MB.
            </p>
          </Dragger>

          {error && (
            <Alert
              message="Upload Error"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
            />
          )}

          {fileList.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <Space>
                <FileTextOutlined />
                <Text>{fileList[0].name}</Text>
                <Text type="secondary">
                  ({(fileList[0].size / 1024 / 1024).toFixed(2)} MB)
                </Text>
              </Space>
            </div>
          )}

          {uploading && (
            <div style={{ marginTop: '16px' }}>
              <Text>Uploading and processing... </Text>
              <Progress percent={uploadProgress} status="active" />
            </div>
          )}

          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleUpload}
            loading={uploading}
            disabled={fileList.length === 0}
            size="large"
          >
            {uploading ? 'Processing...' : 'Upload & Analyze'}
          </Button>
        </Space>
      </Card>

      {/* Results Section */}
      {results && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Summary Statistics */}
          <Card title="Analysis Summary">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Total Transactions"
                  value={results.total_transactions}
                  prefix={<FileTextOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Fraudulent Transactions"
                  value={results.predictions?.filter(p => p.prediction.is_fraud).length || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Fraud Rate"
                  value={results.predictions ? 
                    ((results.predictions.filter(p => p.prediction.is_fraud).length / results.predictions.length) * 100) : 0
                  }
                  precision={2}
                  suffix="%"
                  valueStyle={{ 
                    color: results.predictions && 
                    ((results.predictions.filter(p => p.prediction.is_fraud).length / results.predictions.length) * 100) > 5 
                    ? '#ff4d4f' : '#52c41a' 
                  }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Processing Time"
                  value={results.latency_ms}
                  precision={1}
                  suffix="ms"
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ 
                    color: results.latency_ms > 1000 ? '#ff4d4f' : '#52c41a' 
                  }}
                />
              </Col>
            </Row>
          </Card>

          {/* Charts */}
          <Row gutter={16}>
            <Col span={8}>
              <Card title="Fraud Distribution" size="small">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={getFraudDistributionData()}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={60}
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
                <div style={{ textAlign: 'center', marginTop: '8px' }}>
                  <Space>
                    <Tag color="#52c41a">Legitimate</Tag>
                    <Tag color="#ff4d4f">Fraud</Tag>
                  </Space>
                </div>
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="Probability Distribution" size="small">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={getFraudProbabilityDistribution()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="probability" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="count" fill="#1890ff" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="Processing Performance" size="small">
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={getProcessingTimesData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="batch" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="time" stroke="#52c41a" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {/* Results Table */}
          <Card 
            title="Transaction Analysis Results"
            extra={
              <Button onClick={() => setShowResults(true)}>
                View Full Results
              </Button>
            }
          >
            <Table
              columns={getResultsColumns()}
              dataSource={results.predictions?.slice(0, 10) || []}
              rowKey="transaction_id"
              pagination={false}
              size="small"
              scroll={{ x: true }}
            />
            {results.predictions?.length > 10 && (
              <div style={{ textAlign: 'center', marginTop: '16px' }}>
                <Text type="secondary">
                  Showing 10 of {results.predictions.length} transactions
                </Text>
              </div>
            )}
          </Card>
        </Space>
      )}

      {/* Full Results Modal */}
      <Modal
        title="Full Analysis Results"
        open={showResults}
        onCancel={() => setShowResults(false)}
        footer={null}
        width={1200}
      >
        {results && (
          <Table
            columns={getResultsColumns()}
            dataSource={results.predictions || []}
            rowKey="transaction_id"
            pagination={{ pageSize: 50 }}
            size="small"
            scroll={{ x: true, y: 400 }}
          />
        )}
      </Modal>
    </div>
  );
};

export default FileUpload;
