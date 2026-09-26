import "dotenv/config";
import bcrypt from "bcryptjs";
import { PrismaClient } from "../app/generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

async function main() {
  // First AdminUser — provisioned outside the public UI (spec Assumptions); change this
  // password immediately after first login in a real deployment.
  const seedPasswordHash = await bcrypt.hash("ChangeMe123!", 10);
  await prisma.adminUser.upsert({
    where: { email: "admin@nat.example" },
    update: {},
    create: {
      email: "admin@nat.example",
      passwordHash: seedPasswordHash,
      createdByAdminId: null,
    },
  });

  const portfolioEntries = [
    {
      name: "Riva Restaurant",
      roleDescription: {
        az: "NFC menyu həlli",
        en: "NFC menu solution",
        ru: "Решение NFC-меню",
      },
      bio: {
        az: "Riva üçün NFC kart həllimizi hazırladıq. Artıq qonaqlar sadəcə telefonlarını NFC karta yaxınlaşdıraraq menyuya sürətli və rahat şəkildə keçid edə bilərlər. Rəqəmsal menyu. Sadə, sürətli, müasir.",
        en: "We built an NFC card solution for Riva. Guests now simply tap their phone on the NFC card to instantly reach the menu — a simple, fast, modern digital menu.",
        ru: "Мы разработали решение NFC-карты для Riva. Теперь гости просто подносят телефон к NFC-карте, чтобы мгновенно открыть меню — простое, быстрое и современное цифровое меню.",
      },
      imageUrl: "/brand-assets/portfolio/riva-placeholder.svg",
      externalUrl: null,
      socialLink: null,
      isActive: true,
      displayOrder: 0,
    },
    {
      name: "Elnur Xosratov Barber",
      roleDescription: {
        az: "Tam vebsayt həlli",
        en: "Full website build",
        ru: "Полноценный веб-сайт",
      },
      bio: {
        az: "Sumqayıtda premium kişi bərbərxanası üçün hazırladığımız tam sayt: rezervasiya, xidmət və qiymət siyahısı, qalereya, müştəri rəyləri.",
        en: "A complete website we built for a premium men's barbershop in Sumgait: booking, a service/price list, a gallery, and customer reviews.",
        ru: "Полноценный сайт, который мы создали для премиальной мужской парикмахерской в Сумгайыте: бронирование, список услуг и цен, галерея, отзывы клиентов.",
      },
      imageUrl: "/brand-assets/portfolio/barber-placeholder.svg",
      externalUrl: "https://www.barberxosratov.az/",
      socialLink: null,
      isActive: true,
      displayOrder: 1,
    },
  ];

  for (const entry of portfolioEntries) {
    const existing = await prisma.portfolioEntry.findFirst({ where: { name: entry.name } });
    if (!existing) {
      await prisma.portfolioEntry.create({ data: entry });
    }
  }

  const pricingPlans = [
    {
      tierName: { az: "Başlanğıc", en: "Starter", ru: "Стартовый" },
      price: 49,
      currency: "AZN",
      billingPeriod: "aylıq",
      features: {
        az: ["QR menyu", "1 dil", "Əsas dəstək"],
        en: ["QR menu", "1 language", "Basic support"],
        ru: ["QR меню", "1 язык", "Базовая поддержка"],
      },
      displayOrder: 0,
      isFeatured: false,
    },
    {
      tierName: { az: "Biznes", en: "Business", ru: "Бизнес" },
      price: 99,
      currency: "AZN",
      billingPeriod: "aylıq",
      features: {
        az: ["NFC + QR menyu", "3 dil", "Vebsayt", "Prioritet dəstək"],
        en: ["NFC + QR menu", "3 languages", "Website", "Priority support"],
        ru: ["NFC + QR меню", "3 языка", "Веб-сайт", "Приоритетная поддержка"],
      },
      displayOrder: 1,
      isFeatured: true,
    },
  ];

  for (const plan of pricingPlans) {
    const existing = await prisma.pricingPlan.findFirst({
      where: { tierName: { equals: plan.tierName } },
    });
    if (!existing) {
      await prisma.pricingPlan.create({ data: plan });
    }
  }

  console.log("Seed complete.");
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
