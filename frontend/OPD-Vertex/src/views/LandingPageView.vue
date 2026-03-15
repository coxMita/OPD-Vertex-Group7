<script setup lang="ts">
import { useLandingData } from '@/composables/useLandingData'
import HeroSection from '@/components/LandingPage/HeroSection.vue'
import FeaturesGrid from '@/components/LandingPage/FeaturesGrid.vue'
import HowItWorks from '@/components/LandingPage/HowItWorks.vue'
import StatsStrip from '@/components/LandingPage/StatsStrip.vue'
import TechStack from '@/components/LandingPage/TechStack.vue'
import CtaSection from '@/components/LandingPage/CtaSection.vue'
import AppFooter from '@/components/LandingPage/AppFooter.vue'

const { features, steps, stats, benefits, services } = useLandingData()
</script>

<template>
  <div class="landing-page">
    <HeroSection />
    <FeaturesGrid :features="features" />
    <HowItWorks :steps="steps" />
    <StatsStrip :stats="stats" />
    <TechStack :benefits="benefits" :services="services" />
    <CtaSection />
    <AppFooter />
  </div>
</template>

<style scoped>
.landing-page {
  width: 100%;
  overflow-x: hidden;
}
</style>