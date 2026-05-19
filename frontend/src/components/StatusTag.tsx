import { Tag } from "antd";

import type { LearningStatus } from "../types/learning";

const STATUS_META: Record<LearningStatus, { color: string; label: string }> = {
  not_started: { color: "default", label: "未开始" },
  in_progress: { color: "processing", label: "学习中" },
  assignment_ready: { color: "warning", label: "待完成作业" },
  submitted: { color: "blue", label: "已提交" },
  needs_revision: { color: "error", label: "需修订" },
  mastered: { color: "success", label: "已掌握" },
  review_scheduled: { color: "purple", label: "待复习" },
};

interface StatusTagProps {
  status: LearningStatus;
}

export function StatusTag({ status }: StatusTagProps) {
  const meta = STATUS_META[status];

  return <Tag color={meta.color}>{meta.label}</Tag>;
}
