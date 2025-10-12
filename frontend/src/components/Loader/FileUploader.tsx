import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet } from "lucide-react";
import { Card } from "../../components/ui/card";

interface FileUploaderProps {
  onFileAccepted: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
}

export function FileUploader({
  onFileAccepted,
  accept = {
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-excel": [".xls"],
  },
  maxSize = 10485760, // 10MB
}: FileUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileAccepted(acceptedFiles[0]);
      }
    },
    [onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
  });

  return (
    <Card
      {...getRootProps()}
      className={`border-2 border-dashed p-12 text-center cursor-pointer transition-colors ${
        isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25"
      }`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        {isDragActive ? (
          <Upload className="h-12 w-12 text-primary animate-bounce" />
        ) : (
          <FileSpreadsheet className="h-12 w-12 text-muted-foreground" />
        )}
        <div>
          <p className="text-lg font-medium mb-1">
            {isDragActive ? "Drop the file here" : "Drag & drop your file here"}
          </p>
          <p className="text-sm text-muted-foreground">
            or click to browse • CSV or Excel • Max 10MB
          </p>
        </div>
      </div>
    </Card>
  );
}
