import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Upload, PlayCircle, FileVideo } from 'lucide-react';

const CATEGORIES = [
  'IT/테크',
  '요리/먹방',
  '브이로그',
  '게임',
  '뷰티',
  '교육',
  '운동/건강',
  '음악',
  '여행',
  '리뷰'
];

const ANALYSIS_OPTIONS = [
  { id: 'thumbnail', label: '썸네일 장면 추천 (Best Cut)' },
  { id: 'title', label: '제목 추천 (AI 카피라이팅)' },
  { id: 'compare', label: '경쟁 채널 비교 분석' },
  { id: 'hook', label: '초반 30초 훅(Hook) 진단' },
];

export default function UploadPage() {
  const navigate = useNavigate();
  const [fileName, setFileName] = useState('');
  const [category, setCategory] = useState('');
  const [selectedOptions, setSelectedOptions] = useState<string[]>([
    'thumbnail',
    'title',
    'compare',
    'hook',
  ]);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('video/')) {
      setFileName(file.name);
    }
  };

  const handleOptionToggle = (optionId: string) => {
    setSelectedOptions((prev) =>
      prev.includes(optionId)
        ? prev.filter((id) => id !== optionId)
        : [...prev, optionId]
    );
  };

  const handleStartAnalysis = () => {
    if (!fileName || !category) {
      alert('영상 파일과 카테고리를 선택해주세요.');
      return;
    }
    setShowConfirmDialog(true);
  };

  const handleConfirm = () => {
    setShowConfirmDialog(false);
    navigate('/analysis');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white px-8 py-6 flex justify-between items-center border-b border-gray-100">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-10 h-10 bg-[#F04645] rounded-lg flex items-center justify-center">
            <PlayCircle className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900">Hookly</span>
        </div>
        <Button variant="ghost" onClick={() => navigate('/history')}>
          분석 기록
        </Button>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl mb-2">영상 업로드 및 분석 설정</h1>
          <p className="text-gray-600">분석할 영상을 업로드해주세요.</p>
        </div>

        {/* Upload Area */}
        <Card className="mb-8 overflow-hidden">
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragging
                ? 'border-[#F04645] bg-red-50'
                : fileName
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 bg-white'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept="video/*"
              className="hidden"
              id="video-upload"
              onChange={handleFileChange}
            />
            <label htmlFor="video-upload" className="cursor-pointer">
              {fileName ? (
                <div className="flex flex-col items-center gap-3">
                  <FileVideo className="w-16 h-16 text-green-600" />
                  <div>
                    <p className="text-lg font-semibold text-gray-900">{fileName}</p>
                    <p className="text-sm text-gray-500 mt-1">클릭하여 다른 파일 선택</p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <Upload className="w-16 h-16 text-gray-400" />
                  <div>
                    <p className="text-lg font-semibold text-gray-900">영상 파일을 드래그하거나 클릭하세요</p>
                    <p className="text-sm text-gray-500 mt-1">MP4, MOV, AVI 등 모든 영상 형식 지원</p>
                  </div>
                </div>
              )}
            </label>
          </div>
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
            <p className="text-xs text-gray-600">
              * 업로드한 영상은 분석 목적으로만 사용되며 서버에 저장되지 않습니다.
            </p>
          </div>
        </Card>

        {/* Category Selection */}
        <Card className="mb-8 p-6">
          <Label className="text-base font-semibold mb-3 block">
            카테고리 선택 <span className="text-[#F04645]">(필수)</span>
          </Label>
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="카테고리를 선택하세요" />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {cat}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Card>

        {/* Analysis Options */}
        <Card className="mb-8 p-6">
          <Label className="text-base font-semibold mb-4 block">분석 옵션 선택</Label>
          <div className="space-y-3">
            {ANALYSIS_OPTIONS.map((option) => (
              <div key={option.id} className="flex items-center space-x-2">
                <Checkbox
                  id={option.id}
                  checked={selectedOptions.includes(option.id)}
                  onCheckedChange={() => handleOptionToggle(option.id)}
                />
                <Label
                  htmlFor={option.id}
                  className="text-sm font-normal cursor-pointer"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        </Card>

        {/* Action Button */}
        <Button
          size="lg"
          className="w-full bg-[#F04645] hover:bg-[#d93d3c] text-white py-6 text-lg"
          onClick={handleStartAnalysis}
        >
          AI 분석 시작하기
        </Button>
      </main>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>분석을 시작하시겠습니까?</DialogTitle>
            <DialogDescription asChild>
              <div className="space-y-3 mt-4">
                <div className="flex items-center justify-between py-2 border-b">
                  <span className="text-sm text-gray-600">선택 카테고리:</span>
                  <span className="font-semibold text-gray-900">{category}</span>
                </div>
                <div className="py-2">
                  <p className="text-xs text-gray-500">
                    적용 데이터 기준: 2025.12.31 09:00 업데이트
                  </p>
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              취소
            </Button>
            <Button
              className="bg-[#F04645] hover:bg-[#d93d3c]"
              onClick={handleConfirm}
            >
              확인 및 시작
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
