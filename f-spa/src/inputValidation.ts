export const MAX_NICKNAME_LENGTH = 20;

const NICKNAME_PATTERN = /^[A-Za-z][A-Za-z0-9]{0,19}$/;
const CLASS_CODE_PATTERN = /^\S+$/;

export function sanitizeNicknameInput(rawValue: string): string {
  return rawValue.replace(/\s+/g, "").replace(/[^A-Za-z0-9]/g, "").slice(0, MAX_NICKNAME_LENGTH);
}

export function sanitizeClassCodeInput(rawValue: string): string {
  return rawValue.replace(/\s+/g, "");
}

export function validateNickname(nickname: string): string | null {
  if (!nickname) {
    return "Enter nickname before submitting.";
  }
  if (nickname.length > MAX_NICKNAME_LENGTH) {
    return "Nickname must be 20 characters or fewer.";
  }
  if (!NICKNAME_PATTERN.test(nickname)) {
    if (!/^[A-Za-z]/.test(nickname)) {
      return "Nickname must start with a letter.";
    }
    return "Nickname can contain only letters and numbers (no spaces).";
  }
  return null;
}

export function validateClassCode(classCode: string): string | null {
  if (!classCode) {
    return "Enter class code before submitting.";
  }
  if (!CLASS_CODE_PATTERN.test(classCode)) {
    return "Class code must not contain spaces.";
  }
  return null;
}
