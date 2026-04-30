const crypto = require("crypto");

const keyHex = process.env.SECRET_ENCRYPTION_KEY || "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

if (keyHex.length !== 64) {
  throw new Error("SECRET_ENCRYPTION_KEY debe tener 64 caracteres hexadecimales");
}

const key = Buffer.from(keyHex, "hex");

function encrypt(plaintext) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(String(plaintext), "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();

  return {
    iv: iv.toString("hex"),
    ciphertext: encrypted.toString("hex"),
    authTag: authTag.toString("hex")
  };
}

function decrypt({ iv, ciphertext, authTag }) {
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, Buffer.from(iv, "hex"));
  decipher.setAuthTag(Buffer.from(authTag, "hex"));
  const decrypted = Buffer.concat([
    decipher.update(Buffer.from(ciphertext, "hex")),
    decipher.final()
  ]);
  return decrypted.toString("utf8");
}

module.exports = {
  encrypt,
  decrypt
};
