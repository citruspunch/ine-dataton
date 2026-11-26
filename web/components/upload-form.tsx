"use client";

import { useRef, useState, useTransition } from "react";
import { CloudArrowUp, FileXls, X } from "@phosphor-icons/react/dist/ssr";

import { uploadCase } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { FieldHint, Label } from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ProfileSummary } from "@/lib/types";

const LICENSES = [
  {
    value: "cc-by",
    label: "CC BY verificada",
    hint: "Licencia abierta comprobada en los metadatos del recurso.",
  },
  {
    value: "sin-licencia",
    label: "Sin licencia verificada",
    hint: "Sin una licencia documentada, la validación cierra el recurso.",
  },
];

const ACCEPTED = [".csv", ".xlsx", ".xls"];

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadForm({ profiles }: { profiles: ProfileSummary[] }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState("");
  const [error, setError] = useState("");
  const [profileId, setProfileId] = useState(profiles[0]?.profile_id ?? "");
  const [license, setLicense] = useState("cc-by");
  const [pending, startTransition] = useTransition();

  const selectedProfile = profiles.find((profile) => profile.profile_id === profileId);
  const selectedLicense = LICENSES.find((item) => item.value === license);

  function pick(nextFile: File | null | undefined) {
    if (!nextFile) return;
    const suffix = nextFile.name.slice(nextFile.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED.includes(suffix)) {
      setFileError("Formato no admitido. Use un archivo .csv, .xlsx o .xls.");
      setFile(null);
      return;
    }
    setFileError("");
    setError("");
    setFile(nextFile);
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || !profileId) return;
    const payload = new FormData();
    payload.append("file", file);
    payload.append("profile", profileId);
    payload.append("license", license);
    startTransition(async () => {
      const result = await uploadCase({ ok: true }, payload);
      if (!result.ok) setError(result.message ?? "No se pudo validar el archivo.");
    });
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div>
        <Label htmlFor="file-trigger">Archivo a validar</Label>
        <div
          role="button"
          tabIndex={0}
          aria-controls="file-trigger"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            pick(event.dataTransfer.files?.[0]);
          }}
          className={cn(
            "flex cursor-pointer items-center gap-3 rounded-lg border border-dashed px-4 py-5 transition-colors",
            dragging
              ? "border-accent bg-accent-soft"
              : "border-[#c7c7c7] bg-[#fafafa] hover:border-accent hover:bg-accent-soft/40",
          )}
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-brand shadow-sm">
            {file ? (
              <FileXls className="h-5 w-5" aria-hidden />
            ) : (
              <CloudArrowUp className="h-5 w-5" aria-hidden />
            )}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-[14.5px] font-semibold text-ink">
              {file ? file.name : "Arrastre el archivo o haga clic para seleccionarlo"}
            </span>
            <span className="block text-[13px] text-muted">
              {file
                ? `${formatBytes(file.size)} · listo para validar`
                : "CSV, XLSX o XLS · máximo 20 MB"}
            </span>
          </span>
          {file ? (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                setFile(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              className="rounded-md p-1.5 text-muted hover:bg-white hover:text-fail"
              aria-label="Quitar archivo"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        <input
          ref={inputRef}
          id="file-trigger"
          type="file"
          accept=".csv,.xlsx,.xls"
          className="sr-only"
          onChange={(event) => pick(event.target.files?.[0])}
        />
        {fileError ? <p className="mt-1.5 text-[13px] font-medium text-fail">{fileError}</p> : null}
      </div>

      <div>
        <Label htmlFor="profile-trigger">Perfil declarativo</Label>
        <Select value={profileId} onValueChange={setProfileId}>
          <SelectTrigger id="profile-trigger">
            <SelectValue placeholder="Seleccione un perfil">
              {selectedProfile?.title}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {profiles.map((profile) => (
              <SelectItem key={profile.profile_id} value={profile.profile_id}>
                <span className="flex flex-col py-0.5">
                  <span className="font-medium">{profile.title}</span>
                  <span className="text-[12.5px] text-muted">
                    v{profile.version} · {profile.kind_label}
                  </span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedProfile ? (
          <FieldHint>
            {selectedProfile.description ||
              `Contrato ${selectedProfile.kind_label}${
                selectedProfile.expected_sheet
                  ? ` · hoja ${selectedProfile.expected_sheet}`
                  : ""
              }`}
            {!selectedProfile.valid ? (
              <span className="mt-1 block font-medium text-fail">
                La validación rechazará este perfil porque tiene errores.
              </span>
            ) : null}
          </FieldHint>
        ) : (
          <FieldHint>No hay perfiles. Cree uno con el formulario de nueva regla.</FieldHint>
        )}
      </div>

      <div>
        <Label htmlFor="license-trigger">Licencia del recurso</Label>
        <Select value={license} onValueChange={setLicense}>
          <SelectTrigger id="license-trigger">
            <SelectValue>{selectedLicense?.label}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {LICENSES.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <FieldHint>{selectedLicense?.hint}</FieldHint>
      </div>

      {error ? (
        <p className="rounded-md border border-[#ffb699] bg-fail-bg px-3 py-2 text-[14px] text-fail">
          {error}
        </p>
      ) : null}

      <Button type="submit" disabled={pending || !file || !profileId} className="w-full">
        {pending ? "Evaluando el archivo…" : "Validar archivo"}
      </Button>
    </form>
  );
}
