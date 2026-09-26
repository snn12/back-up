"use client";

import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import { useToast } from "@/components/ui/Toast";

const COUNTRY_CODES = ["+994", "+90", "+7", "+1"];

export default function ContactForm() {
  const t = useTranslations("contact");
  const { showToast } = useToast();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);

    const form = new FormData(event.currentTarget);
    const payload = {
      firstName: form.get("firstName"),
      lastName: form.get("lastName"),
      email: form.get("email"),
      phoneCountryCode: form.get("phoneCountryCode"),
      phoneNumber: form.get("phoneNumber"),
      message: form.get("message"),
      consentAccepted: form.get("consentAccepted") === "on",
    };

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        if (data.errors) setErrors(data.errors);
        showToast(t("error"), "error");
        return;
      }

      showToast(t("success"), "success");
      event.currentTarget.reset();
    } catch {
      showToast(t("error"), "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section id="contact" className="mx-auto max-w-[1280px] px-[var(--spacing-24)] py-[var(--spacing-96)]">
      <div className="mx-auto max-w-[520px] text-center">
        <h2 className="text-[length:var(--text-heading-sm)] font-normal tracking-[-0.02em] text-(--color-bone)">
          {t("heading")}
        </h2>
      </div>

      <form onSubmit={handleSubmit} noValidate className="mx-auto mt-[var(--spacing-60)] flex max-w-[480px] flex-col gap-[var(--spacing-24)]">
        <div className="flex flex-col gap-[var(--spacing-18)] md:flex-row">
          <Field label={t("firstName")} name="firstName" error={errors.firstName} required />
          <Field label={t("lastName")} name="lastName" error={errors.lastName} required />
        </div>

        <Field label={t("email")} name="email" type="email" error={errors.email} required />

        <div className="flex flex-col gap-[var(--spacing-6)]">
          <label className="text-[length:var(--text-caption)] uppercase tracking-[0.025em] text-(--color-ash)">
            {t("phone")}
          </label>
          <div className="flex gap-[var(--spacing-12)]">
            <select
              name="phoneCountryCode"
              defaultValue={COUNTRY_CODES[0]}
              aria-label="Country code"
              className="rounded-(--radius-button) border border-(--color-hairline) bg-transparent px-[var(--spacing-12)] py-[var(--spacing-12)] text-(--color-bone)"
            >
              {COUNTRY_CODES.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
            <input
              name="phoneNumber"
              type="tel"
              required
              className="flex-1 rounded-(--radius-button) border border-(--color-hairline) bg-transparent px-[var(--spacing-18)] py-[var(--spacing-12)] text-(--color-bone) outline-none focus-visible:border-(--color-teal)"
            />
          </div>
          {errors.phoneNumber && <p className="text-[length:var(--text-caption)] text-red-500">{errors.phoneNumber}</p>}
        </div>

        <div className="flex flex-col gap-[var(--spacing-6)]">
          <label htmlFor="message" className="text-[length:var(--text-caption)] uppercase tracking-[0.025em] text-(--color-ash)">
            {t("message")}
          </label>
          <textarea
            id="message"
            name="message"
            rows={5}
            required
            className="rounded-(--radius-card) border border-(--color-hairline) bg-transparent px-[var(--spacing-18)] py-[var(--spacing-12)] text-(--color-bone) outline-none focus-visible:border-(--color-teal)"
          />
          {errors.message && <p className="text-[length:var(--text-caption)] text-red-500">{errors.message}</p>}
        </div>

        <label className="flex items-start gap-[var(--spacing-12)] text-[length:var(--text-caption)] text-(--color-ash)">
          <input type="checkbox" name="consentAccepted" required className="mt-1" />
          {t("consent")}
        </label>
        {errors.consentAccepted && <p className="text-[length:var(--text-caption)] text-red-500">{errors.consentAccepted}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-(--radius-button) bg-(--color-teal) px-[var(--spacing-24)] py-[var(--spacing-18)] text-[length:var(--text-nav-label)] font-semibold uppercase tracking-[0.025em] text-(--color-void) transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {t("submit")}
        </button>
      </form>
    </section>
  );
}

function Field({
  label,
  name,
  type = "text",
  error,
  required,
}: {
  label: string;
  name: string;
  type?: string;
  error?: string;
  required?: boolean;
}) {
  return (
    <div className="flex flex-1 flex-col gap-[var(--spacing-6)]">
      <label htmlFor={name} className="text-[length:var(--text-caption)] uppercase tracking-[0.025em] text-(--color-ash)">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        className="rounded-(--radius-button) border border-(--color-hairline) bg-transparent px-[var(--spacing-18)] py-[var(--spacing-12)] text-(--color-bone) outline-none focus-visible:border-(--color-teal)"
      />
      {error && <p className="text-[length:var(--text-caption)] text-red-500">{error}</p>}
    </div>
  );
}
