import { Card, Statistic, Typography } from "antd";
import type { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  suffix?: ReactNode;
  helperText?: string;
}

export function MetricCard({
  title,
  value,
  suffix,
  helperText,
}: MetricCardProps) {
  return (
    <Card>
      <Statistic title={title} value={value} suffix={suffix} />
      {helperText ? (
        <Typography.Text type="secondary">{helperText}</Typography.Text>
      ) : null}
    </Card>
  );
}
