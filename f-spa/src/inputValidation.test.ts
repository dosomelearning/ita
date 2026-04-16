import { describe, expect, it } from "vitest";
import {
  sanitizeClassCodeInput,
  sanitizeNicknameInput,
  validateClassCode,
  validateNickname,
} from "./inputValidation";

describe("sanitizeNicknameInput", () => {
  it("removes spaces and special characters", () => {
    expect(sanitizeNicknameInput(" Ava_ Novak! ")).toBe("AvaNovak");
  });

  it("caps nickname length at 20 characters", () => {
    expect(sanitizeNicknameInput("ABCDEFGHIJKLMNOPQRSTUVWXYZ")).toBe("ABCDEFGHIJKLMNOPQRST");
  });
});

describe("sanitizeClassCodeInput", () => {
  it("removes spaces and keeps special characters", () => {
    expect(sanitizeClassCodeInput(" ab-12 c$ ")).toBe("ab-12c$");
  });

  it("keeps long values when no spaces are present", () => {
    expect(sanitizeClassCodeInput("class2026!@#")).toBe("class2026!@#");
  });
});

describe("validateNickname", () => {
  it("accepts a valid nickname", () => {
    expect(validateNickname("Ava2026")).toBeNull();
  });

  it("rejects nickname that starts with a number", () => {
    expect(validateNickname("1Ava")).toBe("Nickname must start with a letter.");
  });
});

describe("validateClassCode", () => {
  it("accepts alphanumeric + special characters when no spaces are present", () => {
    expect(validateClassCode("class2026!@#")).toBeNull();
  });

  it("rejects code containing spaces", () => {
    expect(validateClassCode("class 2026")).toBe("Class code must not contain spaces.");
  });
});
